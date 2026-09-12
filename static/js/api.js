// ===== API CLIENT =====
const BASE = '';  // Same origin - no CORS needed

async function apiOnboardPlot(payload) {
  const res = await fetch(`${BASE}/api/v1/plots/onboard`, {
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

async function checkHealth() {
  try {
    const res = await fetch(`${BASE}/health`);
    const data = await res.json();
    const badge = document.getElementById('server-badge');
    if (data.status === 'healthy') {
      badge.textContent = '● Server Online';
      badge.classList.add('connected');
    }
  } catch (e) {
    document.getElementById('server-badge').textContent = '● Server Offline';
  }
}
