// ===== API CLIENT =====
const BASE = '';

// Auth: Request OTP
async function apiRequestOTP(phone, name, state, district) {
  const res = await fetch(`${BASE}/api/v1/auth/request-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      phone_number: phone,
      farmer_name: name,
      state: state,
      district: district
    })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// Auth: Verify OTP
async function apiVerifyOTP(phone, otp) {
  const res = await fetch(`${BASE}/api/v1/auth/verify-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone_number: phone, otp: otp })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// Auth: Get Farmer Profile
async function apiGetFarmerProfile(phone) {
  const res = await fetch(`${BASE}/api/v1/auth/me?phone=${encodeURIComponent(phone)}`);
  if (!res.ok) return null;
  return res.json();
}

// Plots: Onboard with Satellite, Soil & Manual Overrides
async function apiOnboardPlot(payload) {
  const token = localStorage.getItem('kisan_token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE}/api/v1/plots/onboard`, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// Drone: Direct Imagery & Patch Classification
async function apiAnalyzeDroneImage(payload) {
  let options = { method: 'POST' };
  if (payload instanceof FormData) {
    options.body = payload;
  } else {
    options.headers = { 'Content-Type': 'application/json' };
    options.body = JSON.stringify(payload);
  }
  const res = await fetch(`${BASE}/api/v1/drone/analyze-image`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// Pest: CIBRC Diagnosis & DGCA Prescription
async function apiDiagnosePest(payload) {
  const res = await fetch(`${BASE}/api/v1/pest/diagnose`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// Health Check
async function checkHealth() {
  try {
    const res = await fetch(`${BASE}/health`);
    const data = await res.json();
    const badge = document.getElementById('server-badge');
    if (data.status === 'healthy') {
      badge.textContent = '● Live System';
      badge.classList.add('connected');
    }
  } catch (e) {
    const badge = document.getElementById('server-badge');
    if (badge) badge.textContent = '● Connecting...';
  }
}
