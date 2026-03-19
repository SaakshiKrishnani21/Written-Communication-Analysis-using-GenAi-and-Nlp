"""
email_sender.py — HTML Email Notification Service  v2
Sends styled score notifications to students via SMTP.

Configuration (env vars):
  SMTP_HOST   — default: smtp.gmail.com
  SMTP_PORT   — default: 587
  SMTP_USER   — your sending email
  SMTP_PASS   — app password (Gmail: Settings → Security → App Passwords)
"""
import os, smtplib, traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST  = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT  = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER  = os.getenv("SMTP_USER", "")
SMTP_PASS  = os.getenv("SMTP_PASS", "")
FROM_NAME  = "GenAI Assessment System"
APP_URL    = os.getenv("APP_URL", "http://localhost")   # your deployed URL


def _score_band(score: int) -> tuple[str, str]:
    """Return (label, hex_color) for a score."""
    if score >= 85: return "Excellent",   "#22c55e"
    if score >= 70: return "Good",        "#4f8ef7"
    if score >= 55: return "Satisfactory","#f59e0b"
    if score >= 40: return "Below Average","#f97316"
    return "Needs Improvement", "#ef4444"


def send_score_notification(
    to_email: str,
    name: str,
    topic: str,
    score: int,
    feedback: str,
) -> bool:
    """Send AI score notification email. Returns True on success."""
    if not to_email or not SMTP_USER or not SMTP_PASS:
        print(f"Email skipped — SMTP not configured or no recipient.")
        return False

    label, color = _score_band(score)
    short_topic  = (topic[:55] + "…") if len(topic) > 55 else topic
    bar_width    = score  # percent

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0a0d14;font-family:'DM Sans',Arial,sans-serif;color:#e2e8f0">
  <div style="max-width:560px;margin:32px auto;border-radius:16px;overflow:hidden;border:1px solid #1e2d45">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#0d1a2e,#0a1628);padding:28px 32px;border-bottom:1px solid #1e2d45;text-align:center">
      <div style="display:inline-flex;align-items:center;justify-content:center;width:48px;height:48px;background:#4f8ef7;border-radius:12px;font-size:22px;margin-bottom:10px">⚡</div>
      <h1 style="margin:0;font-size:20px;font-weight:700;color:#e2e8f0">Assessment Result</h1>
      <p style="margin:4px 0 0;font-size:13px;color:#94a3b8">GenAI Assessment Platform</p>
    </div>

    <!-- Body -->
    <div style="background:#111827;padding:28px 32px">
      <p style="font-size:15px;margin:0 0 16px">Hi <strong style="color:#e2e8f0">{name}</strong>,</p>
      <p style="font-size:14px;color:#94a3b8;margin:0 0 24px">Your essay on <strong style="color:#e2e8f0">"{short_topic}"</strong> has been evaluated by our AI assessment engine.</p>

      <!-- Score card -->
      <div style="background:#0f1320;border:1px solid #1e2d45;border-radius:12px;padding:24px;text-align:center;margin-bottom:24px">
        <div style="font-size:64px;font-weight:800;color:{color};line-height:1;margin-bottom:4px">{score}</div>
        <div style="font-size:13px;color:#94a3b8;margin-bottom:16px">out of 100 &mdash; <strong style="color:{color}">{label}</strong></div>
        <!-- Progress bar -->
        <div style="background:#1a2235;border-radius:100px;height:8px;overflow:hidden">
          <div style="background:{color};height:100%;width:{bar_width}%;border-radius:100px"></div>
        </div>
      </div>

      <!-- Feedback -->
      <div style="border-left:3px solid #4f8ef7;background:#0d1a2e;border-radius:0 8px 8px 0;padding:14px 16px;margin-bottom:24px">
        <div style="font-size:12px;font-weight:600;color:#4f8ef7;margin-bottom:6px;letter-spacing:0.05em;text-transform:uppercase">AI Feedback</div>
        <div style="font-size:14px;color:#94a3b8;line-height:1.7">{feedback}</div>
      </div>

      <!-- CTA -->
      <div style="text-align:center;margin-bottom:8px">
        <a href="{APP_URL}/frontend/student/past_performance.html"
           style="display:inline-block;background:#4f8ef7;color:#fff;padding:12px 28px;border-radius:8px;font-size:14px;font-weight:600;text-decoration:none">
          View Full Report &rarr;
        </a>
      </div>
    </div>

    <!-- Footer -->
    <div style="background:#0a0d14;padding:14px 32px;text-align:center;border-top:1px solid #1e2d45">
      <p style="font-size:11px;color:#4a5568;margin:0">GenAI Assessment System &bull; Automated notification &bull; Do not reply</p>
    </div>
  </div>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Your Assessment Result: {score}/100 — {short_topic}"
    msg["From"]    = f"{FROM_NAME} <{SMTP_USER}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print(f"✓ Email sent → {to_email}")
        return True
    except Exception:
        print(f"✗ Email failed → {to_email}")
        traceback.print_exc()
        return False


def send_review_notification(
    to_email: str,
    name: str,
    topic: str,
    ai_score: int,
    admin_score: int,
    admin_feedback: str,
) -> bool:
    """Notify student that their essay has been reviewed by admin."""
    if not to_email or not SMTP_USER or not SMTP_PASS:
        return False

    _, ai_color    = _score_band(ai_score)
    _, admin_color = _score_band(admin_score)
    short_topic    = (topic[:55] + "…") if len(topic) > 55 else topic

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0a0d14;font-family:'DM Sans',Arial,sans-serif;color:#e2e8f0">
  <div style="max-width:560px;margin:32px auto;border-radius:16px;overflow:hidden;border:1px solid #1e2d45">
    <div style="background:linear-gradient(135deg,#0d1a2e,#0a1628);padding:28px 32px;border-bottom:1px solid #1e2d45;text-align:center">
      <div style="display:inline-flex;align-items:center;justify-content:center;width:48px;height:48px;background:#22c55e;border-radius:12px;font-size:22px;margin-bottom:10px">✅</div>
      <h1 style="margin:0;font-size:20px;font-weight:700">Admin Review Complete</h1>
      <p style="margin:4px 0 0;font-size:13px;color:#94a3b8">GenAI Assessment Platform</p>
    </div>
    <div style="background:#111827;padding:28px 32px">
      <p style="font-size:15px;margin:0 0 16px">Hi <strong>{name}</strong>,</p>
      <p style="font-size:14px;color:#94a3b8;margin:0 0 24px">An instructor has reviewed your essay on <strong style="color:#e2e8f0">"{short_topic}"</strong>.</p>
      <div style="display:flex;gap:12px;margin-bottom:20px">
        <div style="flex:1;background:#0f1320;border:1px solid #1e2d45;border-radius:10px;padding:16px;text-align:center">
          <div style="font-size:11px;color:#94a3b8;margin-bottom:4px">AI Score</div>
          <div style="font-size:36px;font-weight:800;color:{ai_color}">{ai_score}</div>
        </div>
        <div style="flex:1;background:#0f1320;border:1px solid #1e2d45;border-radius:10px;padding:16px;text-align:center">
          <div style="font-size:11px;color:#94a3b8;margin-bottom:4px">Admin Score</div>
          <div style="font-size:36px;font-weight:800;color:{admin_color}">{admin_score}</div>
        </div>
      </div>
      <div style="border-left:3px solid #22c55e;background:#0d1a2e;border-radius:0 8px 8px 0;padding:14px 16px;margin-bottom:24px">
        <div style="font-size:12px;font-weight:600;color:#22c55e;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.05em">Instructor Feedback</div>
        <div style="font-size:14px;color:#94a3b8;line-height:1.7">{admin_feedback}</div>
      </div>
      <div style="text-align:center">
        <a href="{APP_URL}/frontend/student/past_performance.html"
           style="display:inline-block;background:#22c55e;color:#0a1f0f;padding:12px 28px;border-radius:8px;font-size:14px;font-weight:600;text-decoration:none">
          View Full Comparison Report &rarr;
        </a>
      </div>
    </div>
    <div style="background:#0a0d14;padding:14px 32px;text-align:center;border-top:1px solid #1e2d45">
      <p style="font-size:11px;color:#4a5568;margin:0">GenAI Assessment System &bull; Automated notification</p>
    </div>
  </div>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Admin Review Complete: {admin_score}/100 — {short_topic}"
    msg["From"]    = f"{FROM_NAME} <{SMTP_USER}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print(f"✓ Review email sent → {to_email}")
        return True
    except Exception:
        traceback.print_exc()
        return False