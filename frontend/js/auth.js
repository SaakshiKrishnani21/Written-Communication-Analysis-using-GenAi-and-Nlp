// ── auth.js ──────────────────────────────────────────────────
import { auth, db } from "./firebase.js";
import {
  signInWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  signOut,
  onAuthStateChanged,
  sendPasswordResetEmail
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import {
  doc, getDoc, setDoc, serverTimestamp
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";

const provider = new GoogleAuthProvider();
provider.setCustomParameters({ prompt: "select_account" });

// ── Toast ──────────────────────────────────────────────────────
export function showToast(message, type = "info", duration = 3500) {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }
  const icons = { success: "✓", error: "✕", info: "ℹ" };
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span style="font-size:16px">${icons[type] || "ℹ"}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = "slideOut 0.3s ease forwards";
    setTimeout(() => toast.remove(), 320);
  }, duration);
}

export async function getUserRole(uid) {
  try {
    const snap = await getDoc(doc(db, "users", uid));
    if (snap.exists()) return snap.data().role || "student";
    return "student";
  } catch { return "student"; }
}

export function routeByRole(role) {
  if (role === "admin") window.location.href = "admin/dashboard.html";
  else window.location.href = "student/dashboard.html";
}

async function ensureUserDoc(user, extraData = {}) {
  const ref = doc(db, "users", user.uid);
  const snap = await getDoc(ref);
  if (!snap.exists()) {
    await setDoc(ref, {
      name: user.displayName || extraData.name || "User",
      email: user.email,
      role: "student",
      createdAt: serverTimestamp(),
      ...extraData
    });
  }
  return (await getDoc(ref)).data();
}

export async function loginWithEmail(email, password) {
  const cred = await signInWithEmailAndPassword(auth, email, password);
  const userData = await ensureUserDoc(cred.user);
  return { user: cred.user, role: userData.role };
}

export async function loginWithGoogle() {
  provider.setCustomParameters({ prompt: "select_account" });
  const result = await signInWithPopup(auth, provider);
  const userData = await ensureUserDoc(result.user);
  return { user: result.user, role: userData.role };
}

export async function logout() {
  await signOut(auth);
  window.location.href = "../../login.html";
}

export async function resetPassword(email) {
  await sendPasswordResetEmail(auth, email);
}

export function requireAuth(expectedRole = null) {
  return new Promise((resolve, reject) => {
    const unsub = onAuthStateChanged(auth, async (user) => {
      unsub();
      if (!user) {
        window.location.href = "../../login.html";
        return reject("Not authenticated");
      }
      const role = await getUserRole(user.uid);
      if (expectedRole && role !== expectedRole) {
        if (role === "admin") window.location.href = "../admin/dashboard.html";
        else window.location.href = "../student/dashboard.html";
        return reject("Wrong role");
      }
      resolve({ user, role });
    });
  });
}

export async function populateSidebarUser(user) {
  const snap = await getDoc(doc(db, "users", user.uid));
  const data = snap.exists() ? snap.data() : {};
  const name = data.name || user.displayName || user.email.split("@")[0];
  const role = data.role || "student";
  const initials = name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2) || "U";
  document.querySelectorAll(".user-name").forEach(el => el.textContent = name);
  document.querySelectorAll(".user-role").forEach(el => el.textContent = role.charAt(0).toUpperCase() + role.slice(1));
  document.querySelectorAll(".user-avatar").forEach(el => el.textContent = initials);
  document.querySelectorAll(".logout-btn").forEach(el => { el.style.cursor = "pointer"; el.onclick = logout; });
}