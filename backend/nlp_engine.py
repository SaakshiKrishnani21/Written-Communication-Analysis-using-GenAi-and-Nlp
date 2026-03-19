"""
nlp_engine.py — Essay Scoring Engine  v2
Pipeline:
  1. NLTK extracts structural / lexical features
  2. Google Gemini 1.5 Flash scores 5 dimensions (0-20 each)
  3. Rule-based fallback when Gemini is unavailable
"""
import os, re, json
import nltk
import google.generativeai as genai
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

# ── NLTK bootstrap ─────────────────────────────────────────────
for pkg in ["punkt", "stopwords", "averaged_perceptron_tagger"]:
    try:
        nltk.data.find(f"tokenizers/{pkg}")
    except LookupError:
        nltk.download(pkg, quiet=True)

# ── Gemini config ──────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel("gemini-1.5-flash")

STOP_WORDS = set(stopwords.words("english"))

# Transition / cohesion signal words
TRANSITIONS = [
    "however", "therefore", "furthermore", "moreover", "consequently",
    "in addition", "on the other hand", "in conclusion", "for example",
    "as a result", "similarly", "nevertheless", "thus", "hence",
    "in contrast", "firstly", "secondly", "finally", "in summary",
    "to illustrate", "in particular", "by contrast", "as a consequence",
    "in other words", "that is to say",
]


# ══════════════════════════════════════════════════════════════
#  FEATURE EXTRACTION
# ══════════════════════════════════════════════════════════════
def extract_features(essay: str) -> dict:
    sentences     = sent_tokenize(essay)
    words         = word_tokenize(essay.lower())
    alpha_words   = [w for w in words if w.isalpha()]
    content_words = [w for w in alpha_words if w not in STOP_WORDS]

    word_count      = len(alpha_words)
    sentence_count  = max(len(sentences), 1)
    avg_sent_len    = round(word_count / sentence_count, 1)
    unique_words    = set(content_words)
    ttr             = round(len(unique_words) / max(len(content_words), 1), 3)
    avg_word_len    = round(sum(len(w) for w in content_words) / max(len(content_words), 1), 2)
    paragraphs      = [p.strip() for p in essay.split("\n\n") if p.strip()]
    para_count      = max(len(paragraphs), 1)

    essay_lower      = essay.lower()
    transition_count = sum(1 for t in TRANSITIONS if t in essay_lower)

    # Sentence length variance (higher = more varied writing)
    sent_lengths = [len(word_tokenize(s)) for s in sentences]
    sent_variance = round(
        sum((l - avg_sent_len) ** 2 for l in sent_lengths) / sentence_count, 2
    ) if sentence_count > 1 else 0

    # Presence of conclusion indicators
    has_conclusion = any(c in essay_lower for c in ["in conclusion", "to conclude", "in summary", "to summarise", "finally"])

    return {
        "word_count":      word_count,
        "sentence_count":  sentence_count,
        "avg_sentence_len": avg_sent_len,
        "sentence_variance": sent_variance,
        "vocabulary_richness": ttr,
        "avg_word_length": avg_word_len,
        "paragraph_count": para_count,
        "transition_count": transition_count,
        "unique_words":    len(unique_words),
        "has_conclusion":  has_conclusion,
    }


# ══════════════════════════════════════════════════════════════
#  GEMINI SCORING
# ══════════════════════════════════════════════════════════════
def _gemini_score(topic: str, essay: str, features: dict, domain: str = "") -> dict:
    domain_context = f" (domain: {domain})" if domain else ""
    prompt = f"""You are an expert academic essay evaluator{domain_context}.

TOPIC: "{topic}"

ESSAY:
\"\"\"
{essay}
\"\"\"

NLP FEATURES:
- Words: {features['word_count']} | Sentences: {features['sentence_count']}
- Avg sentence length: {features['avg_sentence_len']} words
- Vocabulary richness (TTR): {features['vocabulary_richness']}
- Paragraph count: {features['paragraph_count']}
- Transition words: {features['transition_count']}
- Has conclusion: {features['has_conclusion']}

Score the essay on exactly 5 dimensions (each 0–20), totalling 100:
1. content_score   — Relevance to topic, depth of argument, supporting evidence
2. structure_score — Introduction/body/conclusion, paragraph organisation, flow
3. language_score  — Vocabulary richness, word choice, style, variety
4. grammar_score   — Grammar, spelling, punctuation, sentence construction
5. critical_thinking_score — Analysis depth, original insight, evaluation of ideas

Respond ONLY with valid JSON — no markdown, no explanation, no preamble:
{{
  "content_score": <int 0-20>,
  "structure_score": <int 0-20>,
  "language_score": <int 0-20>,
  "grammar_score": <int 0-20>,
  "critical_thinking_score": <int 0-20>,
  "total_score": <int 0-100>,
  "feedback": "<2-3 sentences: key strength + most important improvement>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "improvements": ["<improvement 1>", "<improvement 2>", "<improvement 3>"]
}}"""

    try:
        resp = _model.generate_content(prompt)
        raw  = re.sub(r"```json|```", "", resp.text).strip()
        data = json.loads(raw)
        # Clamp values
        for k in ["content_score","structure_score","language_score","grammar_score","critical_thinking_score"]:
            data[k] = max(0, min(20, int(data.get(k, 10))))
        data["total_score"] = sum(data[k] for k in
            ["content_score","structure_score","language_score","grammar_score","critical_thinking_score"])
        return data
    except json.JSONDecodeError:
        # Try to salvage total score
        m = re.search(r'"total_score"\s*:\s*(\d+)', getattr(resp, "text", ""))
        score = int(m.group(1)) if m else 50
        per = score // 5
        return {
            "content_score": per, "structure_score": per,
            "language_score": per, "grammar_score": per,
            "critical_thinking_score": per,
            "total_score": score,
            "feedback": "Essay evaluated. Review scores for details.",
            "strengths": [], "improvements": []
        }
    except Exception as e:
        print(f"Gemini error: {e}")
        return _rule_based(features)


# ══════════════════════════════════════════════════════════════
#  RULE-BASED FALLBACK
# ══════════════════════════════════════════════════════════════
def _rule_based(features: dict) -> dict:
    s = 0

    # Content proxy: word count (0-20)
    wc = features["word_count"]
    s += 20 if wc >= 500 else 15 if wc >= 300 else 10 if wc >= 150 else 5

    # Vocabulary richness (0-20)
    s += min(20, int(features["vocabulary_richness"] * 40))

    # Structure: paragraphs (0-20)
    s += min(20, features["paragraph_count"] * 4)

    # Cohesion: transitions (0-20)
    s += min(20, features["transition_count"] * 3)

    # Sentence variety: avg length in sweet spot (0-20)
    asl = features["avg_sentence_len"]
    s += 20 if 12 <= asl <= 22 else 12 if 8 <= asl <= 28 else 6

    total = min(100, max(0, s))
    per   = total // 5
    return {
        "content_score": per, "structure_score": per,
        "language_score": per, "grammar_score": per,
        "critical_thinking_score": per,
        "total_score": total,
        "feedback": (
            f"Your essay scored {total}/100 using automated feature analysis. "
            "Expand your arguments, add transition words, and ensure a clear structure."
        ),
        "strengths": ["Essay submitted and processed"],
        "improvements": [
            "Increase word count to at least 300 words",
            "Add transition phrases between paragraphs",
            "Include a clear concluding paragraph",
        ],
    }


# ══════════════════════════════════════════════════════════════
#  PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════════
def score_essay(topic: str, essay: str, domain: str = "") -> dict:
    """
    Main scoring function. Returns dict with:
      score, feedback, strengths, improvements, breakdown, nlp_features
    """
    features = extract_features(essay)
    result   = _gemini_score(topic, essay, features, domain)

    return {
        "score":       result["total_score"],
        "feedback":    result.get("feedback", ""),
        "strengths":   result.get("strengths", []),
        "improvements": result.get("improvements", []),
        "breakdown": {
            "content":          result["content_score"],
            "structure":        result["structure_score"],
            "language":         result["language_score"],
            "grammar":          result["grammar_score"],
            "critical_thinking": result["critical_thinking_score"],
        },
        "nlp_features": features,
    }