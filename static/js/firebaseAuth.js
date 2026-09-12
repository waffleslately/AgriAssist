// ===== FIREBASE PHONE AUTH — AgriAssist =====
// Uses Firebase Web SDK v10 (modular ESM via CDN compat shim).
// All OTP generation + SMS sending is 100% handled by Firebase's backend.
// We never generate, mock, or log any OTP value.

import { initializeApp }                       from "https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js";
import { getAuth, RecaptchaVerifier,
         signInWithPhoneNumber, onAuthStateChanged }
                                               from "https://www.gstatic.com/firebasejs/10.12.5/firebase-auth.js";

// ── DOM refs ──────────────────────────────────────────────────────────────
const gate       = document.getElementById('auth-gate');
const stepPhone  = document.getElementById('auth-step-phone');
const stepOtp    = document.getElementById('auth-step-otp');
const phoneInput = document.getElementById('ag-phone-input');
const otpInput   = document.getElementById('ag-otp-input');
const sendBtn    = document.getElementById('ag-send-btn');
const verifyBtn  = document.getElementById('ag-verify-btn');
const resendBtn  = document.getElementById('ag-resend-btn');
const msgEl      = document.getElementById('ag-auth-msg');
const timerEl    = document.getElementById('ag-otp-timer');

let _app, _auth, _confirmationResult, _recaptchaVerifier;
let _resendTimer = null;

// ── Helpers ───────────────────────────────────────────────────────────────
function showMsg(text, isError = false) {
  msgEl.textContent = text;
  msgEl.className   = 'ag-msg ' + (isError ? 'ag-msg-error' : 'ag-msg-info');
  msgEl.style.display = text ? 'block' : 'none';
}

function setBusy(btn, busy, label) {
  btn.disabled    = busy;
  btn.textContent = busy ? '⏳ Please wait…' : label;
}

function startResendTimer(seconds = 60) {
  resendBtn.style.display = 'none';
  let s = seconds;
  timerEl.style.display = 'inline';
  _resendTimer = setInterval(() => {
    timerEl.textContent = `Resend in ${s}s`;
    if (--s < 0) {
      clearInterval(_resendTimer);
      timerEl.style.display = 'none';
      resendBtn.style.display = 'inline-block';
    }
  }, 1000);
}

// ── Init Firebase from backend config ────────────────────────────────────
async function initFirebase() {
  try {
    const res = await fetch('/api/v1/auth/firebase-config');
    if (!res.ok) throw new Error('Firebase config not available on server');
    const cfg = await res.json();
    _app  = initializeApp(cfg);
    _auth = getAuth(_app);
    return true;
  } catch (e) {
    showMsg('Firebase is not configured on this server. Contact the administrator.', true);
    return false;
  }
}

// ── reCAPTCHA setup (invisible) ───────────────────────────────────────────
function setupRecaptcha() {
  if (!_recaptchaVerifier) {
    _recaptchaVerifier = new RecaptchaVerifier(_auth, 'recaptcha-container', {
      size: 'invisible',
      callback: () => {},
    });
  }
}

// ── Step 1: Send OTP ──────────────────────────────────────────────────────
async function sendOtp() {
  const raw   = phoneInput.value.trim().replace(/\s+/g, '');
  const phone = raw.startsWith('+') ? raw : '+91' + raw.replace(/^0/, '');

  if (!/^\+91[6-9]\d{9}$/.test(phone)) {
    showMsg('Please enter a valid 10-digit Indian mobile number.', true);
    return;
  }

  setBusy(sendBtn, true, 'Send OTP');
  showMsg('Sending OTP via Firebase SMS…');

  try {
    setupRecaptcha();
    _confirmationResult = await signInWithPhoneNumber(_auth, phone, _recaptchaVerifier);

    // Switch to OTP step
    stepPhone.style.display = 'none';
    stepOtp.style.display   = 'block';
    otpInput.value          = '';
    otpInput.focus();
    showMsg(`OTP sent to ${phone}. Check your SMS.`);
    startResendTimer(60);
  } catch (err) {
    console.error('[Auth] sendOtp error:', err.code);
    showMsg(friendlyError(err), true);
    // _recaptchaVerifier handles its own reset on failure
  } finally {
    setBusy(sendBtn, false, 'Send OTP');
  }
}

// ── Step 2: Verify OTP ────────────────────────────────────────────────────
async function verifyOtp() {
  const code = otpInput.value.trim();
  if (!/^\d{6}$/.test(code)) {
    showMsg('Please enter the 6-digit code from your SMS.', true);
    return;
  }

  setBusy(verifyBtn, true, 'Verify');
  showMsg('Verifying with Firebase…');

  try {
    const result   = await _confirmationResult.confirm(code);
    const idToken  = await result.user.getIdToken();

    showMsg('OTP verified! Logging you in…');

    // ── POST idToken to our backend for server-side verification + JWT ──
    const backendRes = await fetch('/api/v1/auth/verify-phone', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ id_token: idToken }),
    });

    if (!backendRes.ok) {
      const err = await backendRes.json().catch(() => ({}));
      throw new Error(err.detail || `Backend error ${backendRes.status}`);
    }

    const data = await backendRes.json();

    // Persist session
    localStorage.setItem('kisan_token', data.access_token);
    localStorage.setItem('kisan_phone', data.phone_number);

    // Hide auth gate and reveal the app
    clearInterval(_resendTimer);
    gate.style.display = 'none';
    window._authPhone  = data.phone_number;
    window._authFarmer = data.farmer;
    window.dispatchEvent(new CustomEvent('agri-auth-success', { detail: data }));
  } catch (err) {
    console.error('[Auth] verifyOtp error:', err.code || err.message);
    showMsg(friendlyError(err), true);
  } finally {
    setBusy(verifyBtn, false, 'Verify & Sign In');
  }
}

// ── Resend OTP ────────────────────────────────────────────────────────────
function resendOtp() {
  stepOtp.style.display   = 'none';
  stepPhone.style.display = 'block';
  showMsg('Enter your number again and click Send OTP.');
}

// ── Friendly error messages ───────────────────────────────────────────────
function friendlyError(err) {
  const code = err.code || '';
  if (code.includes('invalid-api-key') || code.includes('api-key-not-valid')) {
    return 'Invalid Firebase API Key. Please add your real Firebase API Key in the backend .env file.';
  }
  if (code.includes('invalid-phone-number'))  return 'Invalid phone number format.';
  if (code.includes('too-many-requests'))      return 'Too many attempts. Please wait a few minutes.';
  if (code.includes('invalid-verification'))   return 'Wrong code. Please try again.';
  if (code.includes('code-expired'))           return 'OTP expired. Please request a new one.';
  if (code.includes('captcha'))                return 'reCAPTCHA failed. Please refresh and try again.';
  return err.message || 'Authentication error. Please try again.';
}

// ── Check existing session on load ───────────────────────────────────────
async function checkExistingSession() {
  const token = localStorage.getItem('kisan_token');
  const phone = localStorage.getItem('kisan_phone');
  if (!token || !phone) return false;

  // Quick backend ping to confirm token is still valid
  try {
    const res = await fetch(`/api/v1/auth/me?phone=${phone}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      const farmer = await res.json();
      window._authPhone  = phone;
      window._authFarmer = farmer;
      window.dispatchEvent(new CustomEvent('agri-auth-success', { detail: { access_token: token, phone_number: phone, farmer } }));
      return true;
    }
  } catch (_) {}
  return false;
}

// ── Bootstrap ─────────────────────────────────────────────────────────────
(async function bootstrap() {
  // 1. Check if already logged in
  if (await checkExistingSession()) {
    gate.style.display = 'none';
    return;
  }

  // 2. Show auth gate + init Firebase
  gate.style.display = 'flex';
  const ok = await initFirebase();
  if (!ok) return;

  // 3. Wire up button events
  sendBtn.addEventListener('click', sendOtp);
  phoneInput.addEventListener('keydown', e => { if (e.key === 'Enter') sendOtp(); });
  verifyBtn.addEventListener('click', verifyOtp);
  otpInput.addEventListener('keydown',  e => { if (e.key === 'Enter') verifyOtp(); });
  resendBtn.addEventListener('click', resendOtp);
})();
