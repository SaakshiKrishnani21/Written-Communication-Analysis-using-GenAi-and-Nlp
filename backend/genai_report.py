"""
genai_report.py — AI Report Generation  v2
Generates:
  - AI narrative evaluation report
  - Admin reviewer report
  - AI-vs-Admin comparison report
All powered by Google Gemini 1.5 Flash.
"""
import os
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel("gemini-1.5-flash")


# ══════════════════════════════════════════════════════════════
#  AI / ADMIN NARRATIVE REPORT
# ══════════════════════════════════════════════════════════════
def generate_ai_report(
    topic: str,
    essay: str,
    result: dict,
    author: str = "AI Engine",
) -> str:
    """
    Generate a detailed narrative evaluation report.
    Works for both AI reports (author='AI Engine') and
    admin reports (author='Admin Reviewer').
    """
    score      = result.get("score", 0)
    feedback   = result.get("feedback", "")
    breakdown  = result.get("breakdown", {})
    strengths  = result.get("strengths", [])
    improvs    = result.get("improvements", [])

    bd_text = ""
    label_map = {
        "content": "Content & Relevance",
        "structure": "Structure & Organisation",
        "language": "Language & Vocabulary",
        "grammar": "Grammar & Mechanics",
        "critical_thinking": "Critical Thinking",
    }
    if breakdown:
        bd_text = "Score breakdown:\n" + "\n".join(
            f"  • {label_map.get(k, k)}: {v}/20"
            for k, v in breakdown.items()
        )

    strengths_text = ("Identified strengths: " + ", ".join(strengths)) if strengths else ""
    improvs_text   = ("Areas for improvement: " + ", ".join(improvs)) if improvs else ""

    score_band = (
        "outstanding" if score >= 85 else
        "strong"      if score >= 70 else
        "satisfactory" if score >= 55 else
        "below average" if score >= 40 else
        "needs significant development"
    )

    prompt = f"""You are an academic evaluator writing a formal assessment report.
Evaluator: {author}
Topic: "{topic}"
Overall score: {score}/100 ({score_band})
{bd_text}
{strengths_text}
{improvs_text}
Summary feedback: {feedback}
Essay excerpt: "{essay[:500]}..."

Write a professional assessment report of 280–380 words in 3 clearly separated paragraphs:

Paragraph 1 — Overall Assessment: Interpret the score, describe the general quality of the essay, and summarise the student's engagement with the topic.

Paragraph 2 — Strengths and Weaknesses: Discuss specific things the student did well (with examples from the essay if possible) and identify the most important areas needing improvement with concrete advice.

Paragraph 3 — Development Recommendations: Provide 2-3 actionable steps the student can take to improve their essay-writing skills. End with an encouraging note.

Write in flowing paragraphs only — no bullet points, no headings, no markdown."""

    try:
        resp = _model.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        print(f"Report generation error: {e}")
        return _fallback_report(topic, score, feedback, author)


def _fallback_report(topic, score, feedback, author):
    band = "excellent" if score >= 85 else "good" if score >= 70 else "satisfactory" if score >= 55 else "below average"
    return (
        f"Assessment Report — Evaluated by {author}\n\n"
        f'This essay on "{topic}" received an overall score of {score}/100, '
        f"which places it in the {band} range. {feedback}\n\n"
        "The assessment has been completed using our standard evaluation framework "
        "covering content relevance, structural organisation, language quality, grammatical "
        "accuracy, and depth of critical thinking. The score reflects the current standard "
        "of the submission across all these dimensions.\n\n"
        "Students are encouraged to review the dimension scores carefully, identify their "
        "weakest areas, and seek additional resources or guidance from their instructors. "
        "Regular practice, wide reading, and structured revision will help improve performance "
        "in future assessments."
    )


# ══════════════════════════════════════════════════════════════
#  AI vs ADMIN COMPARISON REPORT
# ══════════════════════════════════════════════════════════════
def generate_comparison_report(
    topic: str,
    essay: str,
    ai_score: int,
    admin_score: int,
    ai_feedback: str,
    admin_feedback: str,
    ai_report: str = "",
) -> str:
    """
    Generate a comparison report analysing where AI and human
    evaluations agree, diverge, and what each contributes.
    """
    diff        = abs(ai_score - admin_score)
    pct_diff    = round((diff / 100) * 100, 1)
    higher_by   = "AI scored higher" if ai_score > admin_score else ("Admin scored higher" if admin_score > ai_score else "Both scored equally")
    agreement   = "strong" if diff <= 5 else "moderate" if diff <= 15 else "notable"

    prompt = f"""You are an educational assessment analyst writing a comparison report.

Topic: "{topic}"
AI Score:    {ai_score}/100
Admin Score: {admin_score}/100
Score difference: {diff} points ({pct_diff}%) — {agreement} agreement — {higher_by}

AI feedback:    {ai_feedback}
Admin feedback: {admin_feedback}

Write a balanced comparison report of 240–320 words in exactly 3 paragraphs:

Paragraph 1 — Agreement Analysis: Describe where the two evaluations aligned — shared observations, consistent assessments of the essay's quality, and aspects both evaluators agreed on.

Paragraph 2 — Divergence Analysis: Explain what each evaluator emphasised differently. Discuss why the scores differ (if they do), and what each perspective captures that the other may have missed. Be analytical and fair to both approaches.

Paragraph 3 — Student Synthesis: Summarise the combined takeaway for the student — what do both evaluations agree they should focus on? What is the clearest signal from combining AI pattern recognition with human pedagogical judgment? End with a constructive, forward-looking sentence.

Write in flowing paragraphs — no bullet points, no headings, no markdown."""

    try:
        resp = _model.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        print(f"Comparison report error: {e}")
        return _fallback_comparison(topic, ai_score, admin_score, ai_feedback, admin_feedback, diff, agreement)


def _fallback_comparison(topic, ai_score, admin_score, ai_feedback, admin_feedback, diff, agreement):
    return (
        f"Comparison Report for Essay on \"{topic}\"\n\n"
        f"AI Score: {ai_score}/100 | Admin Score: {admin_score}/100 | Difference: {diff} points ({agreement} agreement).\n\n"
        f"AI Assessment: {ai_feedback}\n\n"
        f"Admin Assessment: {admin_feedback}\n\n"
        "This dual-evaluation approach combines automated NLP pattern recognition with human "
        "pedagogical expertise. Students are advised to consider both perspectives when "
        "identifying areas for improvement."
    )