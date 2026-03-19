// ── admin.js ──────────────────────────────────────────────────
import { db } from "./firebase.js";
import { requireAuth, populateSidebarUser } from "./auth.js";
import {
  collection, query, where, getDocs, doc, getDoc,
  addDoc, updateDoc, orderBy, serverTimestamp
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";

const API_BASE = "http://localhost:5000";

export async function initAdminPage() {
  const { user } = await requireAuth("admin");
  await populateSidebarUser(user);
  return user;
}

export async function getAllAssessments(statusFilter = null) {
  let q = statusFilter
    ? query(collection(db, "assessments"), where("status", "==", statusFilter), orderBy("created_at", "desc"))
    : query(collection(db, "assessments"), orderBy("created_at", "desc"));
  const snap = await getDocs(q);
  const assessments = snap.docs.map(d => ({ id: d.id, ...d.data() }));

  return Promise.all(assessments.map(async a => {
    try {
      const uSnap = await getDoc(doc(db, "users", a.student_id));
      const sSnap = await getDoc(doc(db, "students", a.student_id));
      a.student_name = uSnap.exists() ? uSnap.data().name : "Unknown";
      a.student_roll = sSnap.exists() ? sSnap.data().roll_no : "—";
      a.student_branch = sSnap.exists() ? sSnap.data().branch : "—";
      a.student_email = uSnap.exists() ? uSnap.data().email : "—";
    } catch { a.student_name = "Unknown"; }
    return a;
  }));
}

export async function getAssessmentFull(assessmentId) {
  const aSnap = await getDoc(doc(db, "assessments", assessmentId));
  if (!aSnap.exists()) return null;
  const assessment = { id: aSnap.id, ...aSnap.data() };

  const uSnap = await getDoc(doc(db, "users", assessment.student_id));
  const sSnap = await getDoc(doc(db, "students", assessment.student_id));
  assessment.student_name = uSnap.exists() ? uSnap.data().name : "Unknown";
  assessment.student_email = uSnap.exists() ? uSnap.data().email : "—";
  assessment.student_roll = sSnap.exists() ? sSnap.data().roll_no : "—";
  assessment.student_branch = sSnap.exists() ? sSnap.data().branch : "—";

  const rQ = query(collection(db, "reports"), where("assessment_id", "==", assessmentId));
  const rSnap = await getDocs(rQ);
  const report = rSnap.empty ? null : { id: rSnap.docs[0].id, ...rSnap.docs[0].data() };

  const revQ = query(collection(db, "admin_reviews"), where("assessment_id", "==", assessmentId));
  const revSnap = await getDocs(revQ);
  const review = revSnap.empty ? null : { id: revSnap.docs[0].id, ...revSnap.docs[0].data() };

  return { assessment, report, review };
}

export async function submitAdminReview(adminUid, assessmentId, adminScore, adminFeedback) {
  const revRef = await addDoc(collection(db, "admin_reviews"), {
    assessment_id: assessmentId, admin_id: adminUid,
    admin_score: adminScore, admin_feedback: adminFeedback,
    reviewed_at: serverTimestamp()
  });
  await updateDoc(doc(db, "assessments", assessmentId), { status: "reviewed" });

  try {
    const res = await fetch(`${API_BASE}/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ assessment_id: assessmentId, admin_score: adminScore, admin_feedback: adminFeedback })
    });
    if (res.ok) {
      const data = await res.json();
      const rQ = query(collection(db, "reports"), where("assessment_id", "==", assessmentId));
      const rSnap = await getDocs(rQ);
      if (!rSnap.empty) {
        await updateDoc(doc(db, "reports", rSnap.docs[0].id), {
          admin_report: data.admin_report,
          comparison_report: data.comparison_report,
          updated_at: serverTimestamp()
        });
      }
    }
  } catch (err) { console.error("Comparison failed:", err); }

  return revRef.id;
}

export async function getAdminStats() {
  const [allSnap, pendingSnap, reviewedSnap, stuSnap] = await Promise.all([
    getDocs(collection(db, "assessments")),
    getDocs(query(collection(db, "assessments"), where("status", "==", "pending"))),
    getDocs(query(collection(db, "assessments"), where("status", "==", "reviewed"))),
    getDocs(collection(db, "students"))
  ]);
  const all = allSnap.docs.map(d => d.data());
  const scored = all.filter(a => a.ai_score !== null);
  const avgScore = scored.length ? Math.round(scored.reduce((s,a) => s + Number(a.ai_score), 0) / scored.length) : 0;
  return { total: all.length, pending: pendingSnap.size, reviewed: reviewedSnap.size, students: stuSnap.size, avgScore };
}

export function esc(s) {
  return s ? String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;") : "";
}