


// ── firebase.js ──────────────────────────────────────────────
// Replace the config below with your actual Firebase project config
// from: Firebase Console → Project Settings → Your Apps

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";


const firebaseConfig = {
  apiKey: "AIzaSyBJcOb9Mm6EecZkJDSLerVVglgxSJawn1Y",
  authDomain: "genai-assessment-7f11b.firebaseapp.com",
  projectId: "genai-assessment-7f11b",
  storageBucket: "genai-assessment-7f11b.firebasestorage.app",
  messagingSenderId: "99030226434",
  appId: "1:99030226434:web:52afb0e66c71d785d2b91b"
};

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const db = getFirestore(app);
export default app;