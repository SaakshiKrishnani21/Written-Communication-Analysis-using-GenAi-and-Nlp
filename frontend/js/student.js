// ── student.js ───────────────────────────────────────────────
import { db } from "./firebase.js";
import { requireAuth, populateSidebarUser, showToast } from "./auth.js";
import {
  collection, query, where, getDocs, doc, getDoc,
  addDoc, orderBy, serverTimestamp, updateDoc
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";

const API_BASE = "http://localhost:5000";

// ════════════════════════════════════════════════════════════
//  DOMAIN → TOPIC BANK  (random topic generation)
// ════════════════════════════════════════════════════════════
export const DOMAINS = {
  "Computer Science": {
    icon: "💻",
    topics: [
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
    ]
  },
  "Electronics": {
    icon: "⚡",
    topics: [
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
    ]
  },
  "Mechanical": {
    icon: "⚙️",
    topics: [
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
    ]
  },
  "Civil": {
    icon: "🏗️",
    topics: [
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
    ]
  },
  "Biotechnology": {
    icon: "🧬",
    topics: [
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
    ]
  },
  "Information Technology": {
    icon: "🌐",
    topics: [
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
    ]
  },
  "Environment": {
    icon: "🌿",
    topics: [
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
    ]
  },
  "General": {
    icon: "📚",
    topics: [
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
    ]
  }
};

/** Pick a random topic from a domain */
export function getRandomTopic(domainName) {
  const domain = DOMAINS[domainName];
  if (!domain) return "Write about any topic of your choice.";
  const pool = domain.topics;
  return pool[Math.floor(Math.random() * pool.length)];
}

/** Get all domain names */
export function getDomainNames() {
  return Object.keys(DOMAINS);
}

// ════════════════════════════════════════════════════════════
//  AUTH HELPERS
// ════════════════════════════════════════════════════════════
export async function initStudentPage() {
  const { user } = await requireAuth("student");
  await populateSidebarUser(user);
  return user;
}

// ════════════════════════════════════════════════════════════
//  FIRESTORE READS
// ════════════════════════════════════════════════════════════
export async function getStudentProfile(uid) {
  const snap = await getDoc(doc(db, "students", uid));
  return snap.exists() ? snap.data() : null;
}

export async function getStudentAssessments(uid) {
  const q = query(
    collection(db, "assessments"),
    where("student_id", "==", uid),
    orderBy("created_at", "desc")
  );
  const snap = await getDocs(q);
  return snap.docs.map(d => ({ id: d.id, ...d.data() }));
}

export async function getAssessmentDetails(assessmentId) {
  const aSnap = await getDoc(doc(db, "assessments", assessmentId));
  if (!aSnap.exists()) return null;
  const assessment = { id: aSnap.id, ...aSnap.data() };

  const rQ = query(collection(db, "reports"), where("assessment_id", "==", assessmentId));
  const rSnap = await getDocs(rQ);
  const report = rSnap.empty ? null : { id: rSnap.docs[0].id, ...rSnap.docs[0].data() };

  const revQ = query(collection(db, "admin_reviews"), where("assessment_id", "==", assessmentId));
  const revSnap = await getDocs(revQ);
  const review = revSnap.empty ? null : { id: revSnap.docs[0].id, ...revSnap.docs[0].data() };

  return { assessment, report, review };
}

// ════════════════════════════════════════════════════════════
//  SUBMIT ASSESSMENT
// ════════════════════════════════════════════════════════════
export async function submitAssessment(uid, topic, essay, domain = "") {
  const docRef = await addDoc(collection(db, "assessments"), {
    student_id: uid, topic, essay, domain,
    ai_score: null, status: "pending",
    created_at: serverTimestamp()
  });

  try {
    const res = await fetch(`${API_BASE}/score`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ assessment_id: docRef.id, topic, essay, domain })
    });
    if (!res.ok) throw new Error("Backend error");
    const data = await res.json();

    await updateDoc(doc(db, "assessments", docRef.id), {
      ai_score: data.score, ai_feedback: data.feedback,
      ai_breakdown: data.breakdown || {}, status: "scored"
    });

    await addDoc(collection(db, "reports"), {
      assessment_id: docRef.id, student_id: uid,
      ai_report: data.report, admin_report: null,
      comparison_report: null, created_at: serverTimestamp()
    });

    return { id: docRef.id, score: data.score, feedback: data.feedback, breakdown: data.breakdown };
  } catch (err) {
    console.error("AI scoring failed:", err);
    return { id: docRef.id, score: null, feedback: null, error: err.message };
  }
}

// ════════════════════════════════════════════════════════════
//  STATS & DISPLAY HELPERS
// ════════════════════════════════════════════════════════════
export function calcPerformanceStats(assessments) {
  const scored = assessments.filter(a => a.ai_score !== null);
  if (!scored.length) return { avg: 0, highest: 0, lowest: 0, total: assessments.length, pending: assessments.length, scored: 0 };
  const scores = scored.map(a => Number(a.ai_score));
  return {
    total: assessments.length, scored: scored.length,
    pending: assessments.length - scored.length,
    avg: Math.round(scores.reduce((s, v) => s + v, 0) / scores.length),
    highest: Math.max(...scores), lowest: Math.min(...scores)
  };
}

export function scoreColor(score) {
  if (score >= 75) return "green";
  if (score >= 50) return "amber";
  return "red";
}

export function scoreBadgeClass(score) {
  if (score >= 75) return "badge-green";
  if (score >= 50) return "badge-amber";
  return "badge-red";
}

export function scoreLabel(score) {
  if (score >= 85) return "Excellent";
  if (score >= 70) return "Good";
  if (score >= 50) return "Average";
  return "Needs Work";
}

export function esc(s) {
  if (!s) return "";
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}