"""
app.py — GenAI Assessment Flask Backend  v2
Run: python app.py
Endpoints:
  POST /score      — score an essay with Gemini + NLTK
  POST /compare    — generate admin-vs-AI comparison report
  GET  /topics     — return random topic(s) for a domain (server-side variant)
  GET  /health     — health check
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from nlp_engine import score_essay
from genai_report import generate_ai_report, generate_comparison_report
from email_sender import send_score_notification
import os, random

app = Flask(__name__)
CORS(app, origins=["*"])          # Tighten to your domain in production

# ── Firebase Admin SDK ─────────────────────────────────────────
# Place serviceAccountKey.json in backend/ or set GOOGLE_APPLICATION_CREDENTIALS
_cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "serviceAccountKey.json")
if os.path.exists(_cred_path):
    cred = credentials.Certificate(_cred_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    _fb_ready = True
else:
    print("⚠ serviceAccountKey.json not found – Firestore writes disabled.")
    db = None
    _fb_ready = False

# ── Server-side topic bank (mirrors frontend JS) ───────────────
TOPIC_BANK = {
    "Computer Science": [
        "The Role of Machine Learning in Cybersecurity",
        "Edge Computing vs Cloud Computing: A Comparative Analysis",
        "Quantum Computing: Opportunities and Challenges",
        "Ethical Implications of Artificial Intelligence",
        "The Future of Human-Computer Interaction",
        "Blockchain Technology Beyond Cryptocurrency",
        "Open Source Software: Benefits and Risks",
        "The Impact of Big Data on Decision Making",
        "Federated Learning: Privacy-Preserving AI",
        "Autonomous Systems and Robotics in Industry",
    ],
    "Electronics": [
        "Internet of Things: Connecting the Physical World",
        "5G Technology and Its Societal Impact",
        "Neuromorphic Computing: Brain-Inspired Chips",
        "VLSI Design Trends and Challenges",
        "Wearable Electronics and Health Monitoring",
        "Printed Electronics and Flexible Circuits",
        "Power Electronics in Renewable Energy Systems",
        "Nanotechnology in Semiconductor Manufacturing",
        "Signal Processing in Modern Communication",
        "MEMS Devices and Their Applications",
    ],
    "Mechanical": [
        "Additive Manufacturing: Revolutionising Production",
        "The Role of Robotics in Modern Manufacturing",
        "Sustainable Engineering and Green Design",
        "Advanced Materials in Aerospace Engineering",
        "Computational Fluid Dynamics in Engineering",
        "Industry 4.0 and Smart Manufacturing",
        "Electric Vehicles: Engineering Challenges",
        "Nanotechnology Applications in Mechanical Engineering",
        "Biomechanics and Medical Device Design",
        "Lean Manufacturing Principles and Practices",
    ],
    "Civil": [
        "Smart Cities: Infrastructure for the Future",
        "Sustainable Construction Materials and Methods",
        "Climate Change Adaptation in Urban Planning",
        "Earthquake-Resistant Structural Design",
        "Water Resource Management in Urban Areas",
        "Green Building Certification and Practices",
        "Transportation Infrastructure and Mobility",
        "Remote Sensing in Geotechnical Engineering",
        "Waste Management Strategies in Developing Cities",
        "Digital Twins in Civil Infrastructure",
    ],
    "Biotechnology": [
        "CRISPR-Cas9: Gene Editing Ethics and Applications",
        "Bioinformatics and Personalised Medicine",
        "Stem Cell Therapy: Promise and Reality",
        "Synthetic Biology and Bioengineering",
        "Vaccine Development in the Post-COVID Era",
        "Agricultural Biotechnology and Food Security",
        "Bioremediation of Environmental Pollutants",
        "Microbiome Research and Human Health",
        "Biosensors for Disease Diagnosis",
        "Marine Biotechnology and Blue Economy",
    ],
    "Information Technology": [
        "Zero Trust Security Architecture",
        "Cloud Migration Strategies for Enterprises",
        "DevOps Culture and Continuous Delivery",
        "Digital Transformation in Healthcare",
        "Data Privacy Regulations and Compliance",
        "Microservices vs Monolithic Architecture",
        "AI-Driven Business Intelligence",
        "Augmented Reality in E-Commerce",
        "Low-Code Platforms: Democratising Development",
        "Green IT and Sustainable Data Centres",
    ],
    "Environment": [
        "Renewable Energy Transition: Barriers and Solutions",
        "Carbon Capture and Storage Technologies",
        "Biodiversity Conservation in the Anthropocene",
        "Circular Economy and Waste Reduction",
        "Environmental Impact of Fast Fashion",
        "Ocean Plastic Pollution: Causes and Solutions",
        "Urban Heat Islands and Green Infrastructure",
        "Nuclear Energy as a Climate Solution",
        "Sustainable Agriculture and Food Systems",
        "Environmental Justice in Developing Nations",
    ],
    "General": [
        "The Impact of Social Media on Mental Health",
        "Remote Work: Benefits and Challenges",
        "Universal Basic Income: A Viable Solution?",
        "Space Exploration: Worth the Investment?",
        "Digital Literacy in the 21st Century",
        "Globalisation and Cultural Identity",
        "The Ethics of Artificial Intelligence in Society",
        "Misinformation and the Role of Media",
        "Future of Education in a Digital World",
        "Income Inequality and Economic Mobility",
    ],
}


# ── GET /topics ────────────────────────────────────────────────
@app.route("/topics", methods=["GET"])
def get_topics():
    """
    Return a random topic (or list) for a given domain.
    Query params:
      domain  — domain name (required)
      count   — how many topics to return (default 1)
    """
    domain = request.args.get("domain", "General")
    count  = min(int(request.args.get("count", 1)), 5)
    pool   = TOPIC_BANK.get(domain, TOPIC_BANK["General"])
    topics = random.sample(pool, min(count, len(pool)))
    return jsonify({"domain": domain, "topics": topics, "count": len(topics)})


# ── POST /score ────────────────────────────────────────────────
@app.route("/score", methods=["POST"])
def score():
    """
    Score an essay.
    Body: { assessment_id, topic, essay, domain? }
    Returns: { score, feedback, report, breakdown, nlp_features }
    """
    data          = request.get_json(force=True)
    assessment_id = data.get("assessment_id")
    topic         = data.get("topic", "")
    essay         = data.get("essay", "")
    domain        = data.get("domain", "General")

    if not essay.strip() or not topic.strip():
        return jsonify({"error": "Missing topic or essay"}), 400

    # Run NLP + AI scoring
    result = score_essay(topic, essay, domain)

    # Generate full AI narrative report
    report_text = generate_ai_report(topic, essay, result)

    # Optionally send email to student
    if _fb_ready and assessment_id:
        try:
            a_ref  = db.collection("assessments").document(assessment_id).get()
            if a_ref.exists:
                sid    = a_ref.to_dict().get("student_id", "")
                u_ref  = db.collection("users").document(sid).get()
                if u_ref.exists:
                    udata  = u_ref.to_dict()
                    send_score_notification(
                        to_email=udata.get("email", ""),
                        name=udata.get("name", "Student"),
                        topic=topic,
                        score=result["score"],
                        feedback=result["feedback"],
                    )
        except Exception as e:
            print(f"Email error: {e}")

    return jsonify({
        "score":        result["score"],
        "feedback":     result["feedback"],
        "report":       report_text,
        "breakdown":    result.get("breakdown", {}),
        "nlp_features": result.get("nlp_features", {}),
        "strengths":    result.get("strengths", []),
        "improvements": result.get("improvements", []),
    })


# ── POST /compare ──────────────────────────────────────────────
@app.route("/compare", methods=["POST"])
def compare():
    """
    Generate admin-vs-AI comparison report.
    Body: { assessment_id, admin_score, admin_feedback }
    Returns: { admin_report, comparison_report }
    """
    data          = request.get_json(force=True)
    assessment_id = data.get("assessment_id")
    admin_score   = int(data.get("admin_score", 0))
    admin_feedback = data.get("admin_feedback", "")

    if not _fb_ready:
        return jsonify({"error": "Firestore not configured"}), 503

    # Fetch assessment
    a_snap = db.collection("assessments").document(assessment_id).get()
    if not a_snap.exists:
        return jsonify({"error": "Assessment not found"}), 404

    a          = a_snap.to_dict()
    topic      = a.get("topic", "")
    essay      = a.get("essay", "")
    ai_score   = a.get("ai_score", 0)
    ai_feedback = a.get("ai_feedback", "")

    # Fetch existing AI report
    r_query = (db.collection("reports")
                 .where("assessment_id", "==", assessment_id)
                 .limit(1).get())
    ai_report = r_query[0].to_dict().get("ai_report", "") if r_query else ""

    # Generate reports
    admin_report = generate_ai_report(
        topic, essay,
        {"score": admin_score, "feedback": admin_feedback, "breakdown": {}},
        author="Admin Reviewer"
    )
    comparison = generate_comparison_report(
        topic=topic, essay=essay,
        ai_score=ai_score, admin_score=admin_score,
        ai_feedback=ai_feedback, admin_feedback=admin_feedback,
        ai_report=ai_report,
    )

    return jsonify({
        "admin_report":       admin_report,
        "comparison_report":  comparison,
    })


# ── GET /health ────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":   "ok",
        "service":  "GenAI Assessment Backend v2",
        "firebase": _fb_ready,
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)