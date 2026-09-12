// ===== APP LOGIC =====

// ── Set default sowing date to 23 days ago ──
const sowDate = new Date();
sowDate.setDate(sowDate.getDate() - 23);
document.getElementById('sowing-date').value = sowDate.toISOString().split('T')[0];

// ── Tab switching ──
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.dataset.tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${tab}`).classList.add('active');
  });
});

// ── Health check on load ──
checkHealth();

// =============================
// PLOT ONBOARDING FORM
// =============================
document.getElementById('submit-btn').addEventListener('click', async () => {
  if (!window.currentCoords) return;

  const payload = {
    phone_number: document.getElementById('phone').value.trim(),
    farmer_name:  document.getElementById('farmer-name').value.trim(),
    state:        document.getElementById('state').value,
    district:     document.getElementById('district').value.trim(),
    village:      document.getElementById('village').value.trim() || null,
    language:     document.getElementById('language').value,
    plot_name:    'Main Field',
    boundary:     { type: 'Polygon', coordinates: [window.currentCoords] },
    crop_name:    document.getElementById('crop-name').value,
    variety:      document.getElementById('variety').value.trim() || null,
    season:       document.getElementById('season').value,
    sowing_date:  document.getElementById('sowing-date').value,
    irrigation_source: document.getElementById('irrigation').value,
    soil_texture: document.getElementById('soil-texture').value
  };

  showLoading();
  try {
    const data = await apiOnboardPlot(payload);
    hideLoading();
    renderResults(data, document.getElementById('language').value);
  } catch (e) {
    hideLoading();
    renderError(e.message);
  }
});

// =============================
// PEST DIAGNOSIS FORM
// =============================
document.getElementById('pest-btn').addEventListener('click', async () => {
  // Dummy IDs for demo without a real plot
  const demoPlotId = '00000000-0000-0000-0000-000000000001';
  const demoCropId = '00000000-0000-0000-0000-000000000002';

  const payload = {
    plot_id:      demoPlotId,
    crop_cycle_id: demoCropId,
    crop_name:    document.getElementById('pest-crop').value,
    pest_key:     document.getElementById('pest-key').value,
    severity_observed_pct: parseFloat(document.getElementById('severity-slider').value),
    drone_spray_requested: document.getElementById('drone-spray').checked
  };

  showLoading();
  try {
    const data = await apiDiagnosePest(payload);
    hideLoading();
    renderPestResults(data);
  } catch (e) {
    hideLoading();
    renderError(e.message);
  }
});

// =============================
// LOADING
// =============================
let loadingTimer;
function showLoading() {
  document.getElementById('loading-overlay').style.display = 'flex';
  const steps = ['ls-1','ls-2','ls-3','ls-4','ls-5'];
  steps.forEach(s => document.getElementById(s).classList.remove('active'));
  document.getElementById('ls-1').classList.add('active');
  let i = 1;
  loadingTimer = setInterval(() => {
    if (i < steps.length) {
      document.getElementById(steps[i-1]).classList.remove('active');
      document.getElementById(steps[i]).classList.add('active');
      i++;
    }
  }, 900);
}
function hideLoading() {
  clearInterval(loadingTimer);
  document.getElementById('loading-overlay').style.display = 'none';
}

// =============================
// RENDER PLOT RESULTS
// =============================
function renderResults(data, lang) {
  document.getElementById('results-placeholder').style.display = 'none';
  const el = document.getElementById('results-content');
  el.style.display = 'block';

  const rec = data.recommendation;
  const soil = data.soil_profile;
  const sat = data.satellite;
  const wx = data.weather;
  const plot = data.plot;
  const crop = data.crop;
  const localText = rec.localized_text || '';

  // NDVI status label
  const ndvi = sat.mean_ndvi;
  let ndviStatus, ndviClass;
  if (ndvi >= 0.55) { ndviStatus = 'Healthy / Vigorous'; ndviClass = 'status-green'; }
  else if (ndvi >= 0.38) { ndviStatus = 'Moderate'; ndviClass = 'status-amber'; }
  else { ndviStatus = 'Stressed / Low Vigor'; ndviClass = 'status-red'; }

  // Soil status badges
  function soilBadge(status) {
    const cls = status === 'Low' ? 'status-red' : status === 'High' ? 'status-green' : 'status-amber';
    return `<span class="status-badge ${cls}">${status}</span>`;
  }

  const fertRows = (rec.fertilizer_schedule || []).map(f => {
    const icons = { Urea: '🟡', DAP: '🟤', MOP: '🔵' };
    const icon = Object.keys(icons).find(k => f.fertilizer.includes(k)) || '🌿';
    return `
    <div class="fert-row">
      <div class="fert-icon">${icons[icon] || '🌿'}</div>
      <div class="fert-info">
        <div class="fert-name">${f.fertilizer}</div>
        <div class="fert-dose">${f.timing_stage}</div>
        <div class="fert-dose" style="color:#64748b;margin-top:3px">${f.instructions.substring(0,80)}...</div>
      </div>
      <div class="fert-bags">
        <div class="fert-bags-val">${f.bags_per_acre}</div>
        <div class="fert-bags-label">bags/acre</div>
        <div class="fert-bags-label">${f.quantity_kg_per_acre} kg/acre</div>
      </div>
    </div>`;
  }).join('');

  const ndviPct = Math.min(100, Math.max(0, ((ndvi + 1) / 2) * 100));

  const rainWarnHtml = rec.weather_warning ?
    `<div class="result-card" style="border-color:#fca5a5;background:#fff1f2">
       <div class="result-card-header">
         <div class="result-card-icon">⚠️</div>
         <div>
           <div class="result-card-title" style="color:#dc2626">Rain Alert – Delay Top Dressing</div>
           <div class="result-card-sub">Heavy rain forecast in next 48h</div>
         </div>
       </div>
       <p style="font-size:12px;color:#9f1239">${wx.precipitation_48h_mm} mm of rain expected. Hold broadcasting until rain stops to prevent nitrogen runoff.</p>
     </div>` : '';

  el.innerHTML = `
    <!-- Plot Summary -->
    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">📍</div>
        <div>
          <div class="result-card-title">${plot.name} &nbsp;·&nbsp; ${crop.crop_name}</div>
          <div class="result-card-sub">${crop.stage} · Day ${crop.days_after_sowing}</div>
        </div>
      </div>
      <div class="metric-grid">
        <div class="metric-box">
          <div class="metric-val">${plot.area_acres}</div>
          <div class="metric-label">Acres</div>
        </div>
        <div class="metric-box">
          <div class="metric-val">Day ${crop.days_after_sowing}</div>
          <div class="metric-label">After Sowing</div>
        </div>
      </div>
    </div>

    ${rainWarnHtml}

    <!-- Satellite Health -->
    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🛰️</div>
        <div>
          <div class="result-card-title">Satellite Health (NDVI)</div>
          <div class="result-card-sub">${sat.source}</div>
        </div>
      </div>
      <div class="ndvi-bar-wrap">
        <div class="ndvi-bar-bg">
          <div class="ndvi-marker" style="left:${ndviPct}%"></div>
        </div>
        <div class="ndvi-val">${ndvi}</div>
      </div>
      <div style="margin-top:8px;display:flex;gap:8px;align-items:center">
        <span class="status-badge ${ndviClass}">${ndviStatus}</span>
        <span style="font-size:11px;color:#64748b">Moisture: ${sat.soil_moisture_proxy}</span>
      </div>
    </div>

    <!-- Soil Status -->
    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🌍</div>
        <div>
          <div class="result-card-title">Soil Health Profile</div>
          <div class="result-card-sub">${soil.source} ${soil.distance_km ? '· ' + soil.distance_km + ' km away' : '(District Benchmark)'}</div>
        </div>
      </div>
      <div class="nutrient-grid">
        ${['nitrogen','phosphorus','potassium'].map(n => {
          const val = data.recommendation.fertilizer_schedule.length ? 
            (n==='nitrogen'?soil.available_nitrogen_kg_ha:n==='phosphorus'?soil.available_phosphorus_kg_ha:soil.available_potassium_kg_ha) : 0;
          const label = {nitrogen:'N',phosphorus:'P',potassium:'K'}[n];
          // derive status from soil values (rough approximation)
          const thresholds = {nitrogen:[280,560], phosphorus:[23,56], potassium:[140,330]};
          const [lo, hi] = thresholds[n];
          const status = val < lo ? 'Low' : val > hi ? 'High' : 'Medium';
          const cls = status.toLowerCase();
          return `<div class="nutrient-box ${cls}">
            <div class="nutrient-name">${label} (${label === 'N' ? 'kg/ha' : 'kg/ha'})</div>
            <div class="nutrient-status">${status}</div>
            <div style="font-size:10px;opacity:.7">${val}</div>
          </div>`;
        }).join('')}
      </div>
      <div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:6px;font-size:11px;color:#64748b">
        <span>pH: ${soil.ph}</span>·
        <span>OC: ${soil.organic_carbon_pct}%</span>·
        <span>EC: ${soil.electrical_conductivity} dS/m</span>
      </div>
    </div>

    <!-- Weather -->
    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🌤️</div>
        <div>
          <div class="result-card-title">7-Day Weather Forecast</div>
          <div class="result-card-sub">Open-Meteo</div>
        </div>
      </div>
      <div class="weather-row"><span class="weather-key">Max Temp</span><span class="weather-val">${wx.max_temp}°C</span></div>
      <div class="weather-row"><span class="weather-key">Min Temp</span><span class="weather-val">${wx.min_temp}°C</span></div>
      <div class="weather-row"><span class="weather-key">Rain (next 48h)</span>
        <span class="weather-val">
          ${wx.precipitation_48h_mm} mm
          ${wx.heavy_rain_warning ? '<span class="status-badge status-red" style="margin-left:6px">⚠️ Heavy Rain</span>' : '<span class="status-badge status-green" style="margin-left:6px">✅ Clear</span>'}
        </span>
      </div>
    </div>

    <!-- Fertilizer Plan -->
    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🌿</div>
        <div>
          <div class="result-card-title">Fertilizer Prescription</div>
          <div class="result-card-sub">ICAR Package of Practices · Commercial Bags</div>
        </div>
      </div>
      ${fertRows || '<p style="font-size:12px;color:#64748b">No chemical fertilizer required at this stage.</p>'}
    </div>

    <!-- Localized Advisory Card -->
    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">📋</div>
        <div>
          <div class="result-card-title">Localized Advisory</div>
        </div>
      </div>
      <div class="advisory-lang-toggle">
        <button class="lang-btn ${lang==='hi'?'active':''}" onclick="switchLang('hi',this)">हिंदी</button>
        <button class="lang-btn ${lang==='en'?'active':''}" onclick="switchLang('en',this)">English</button>
      </div>
      <div class="advisory-text" id="advisory-text">${localText}</div>
    </div>
  `;

  window._advisoryLocalized = localText;
  window._advisoryEn = localText;

  // Scroll to top of results
  el.parentElement.scrollTop = 0;
}

// Language switch for advisory
window.switchLang = function(lang, btn) {
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  // We store both langs from the raw response
  const key = lang === 'hi' ? '_advisoryHi' : '_advisoryEn';
  const txt = window[key] || window._advisoryLocalized || '';
  document.getElementById('advisory-text').textContent = txt;
};

// =============================
// RENDER PEST RESULTS
// =============================
function renderPestResults(data) {
  document.getElementById('results-placeholder').style.display = 'none';
  const el = document.getElementById('results-content');
  el.style.display = 'block';

  const etl = data.economic_threshold_breached;
  const dp = data.drone_spray_prescription;
  const fp = dp?.flight_parameters || {};

  const bioCtrl = data.ipm_measures?.biological || {};
  const chemCtrl = data.ipm_measures?.chemical || {};
  const cultural = data.ipm_measures?.cultural || [];

  el.innerHTML = `
    <!-- Diagnosis -->
    <div class="result-card" style="${etl ? 'border-color:#fca5a5;background:#fff7f7' : ''}">
      <div class="result-card-header">
        <div class="result-card-icon">🐛</div>
        <div>
          <div class="result-card-title">${data.pest_name}</div>
          <div class="result-card-sub">${data.scientific_name || ''}</div>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
        <span class="status-badge ${etl ? 'status-red' : 'status-green'}">
          ${etl ? '🚨 ETL Breached' : '✅ Below ETL'}
        </span>
        <span style="font-size:12px;color:#64748b">Severity: ${data.severity_observed_pct}%</span>
      </div>
      <div style="font-size:11px;color:#64748b;background:#f8fafc;padding:8px;border-radius:6px;border:1px solid #e2e8f0">
        📌 ETL Standard: ${data.etl_guideline}
      </div>
    </div>

    <!-- Cultural measures -->
    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🪤</div>
        <div><div class="result-card-title">Cultural / Mechanical Control</div></div>
      </div>
      ${cultural.map(m => `<div style="font-size:12px;color:#475569;padding:5px 0;border-bottom:1px solid #f1f5f9">• ${m}</div>`).join('')}
    </div>

    <!-- Biological -->
    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🍃</div>
        <div>
          <div class="result-card-title">Biological Control</div>
          <div class="result-card-sub">ICAR Approved</div>
        </div>
      </div>
      <div class="weather-row"><span class="weather-key">Product</span><span class="weather-val">${bioCtrl.name || '-'}</span></div>
      <div class="weather-row"><span class="weather-key">Dosage</span><span class="weather-val">${bioCtrl.dosage_per_acre || '-'}</span></div>
      <div class="weather-row"><span class="weather-key">Timing</span><span class="weather-val">${bioCtrl.timing || '-'}</span></div>
    </div>

    <!-- Chemical -->
    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🧪</div>
        <div>
          <div class="result-card-title">Chemical Treatment (CIBRC)</div>
          <div class="result-card-sub">${chemCtrl.trade_examples || ''}</div>
        </div>
      </div>
      <div class="weather-row"><span class="weather-key">Active Ingredient</span><span class="weather-val" style="font-size:11px">${chemCtrl.active_ingredient || '-'}</span></div>
      <div class="weather-row"><span class="weather-key">Knapsack Dose</span><span class="weather-val" style="font-size:11px">${chemCtrl.dosage_knapsack_per_acre || '-'}</span></div>
      <div class="weather-row"><span class="weather-key">Pre-Harvest Interval</span><span class="weather-val">${chemCtrl.waiting_period_days || '-'} days</span></div>
    </div>

    <!-- Drone Spray -->
    ${dp?.applicable ? `
    <div class="result-card" style="border-color:#bae6fd;background:#f0f9ff">
      <div class="result-card-header">
        <div class="result-card-icon">🚁</div>
        <div>
          <div class="result-card-title" style="color:#0369a1">DGCA Drone Spray Mission</div>
          <div class="result-card-sub">Ultra-Low Volume (ULV) – 10 L/acre</div>
        </div>
      </div>
      <div class="drone-param"><span class="drone-param-key">Water Volume</span><span class="drone-param-val">${dp.drone_water_volume_litres} L total</span></div>
      <div class="drone-param"><span class="drone-param-key">Chemical Rate</span><span class="drone-param-val">${dp.chemical_rate_per_acre}</span></div>
      <div class="drone-param"><span class="drone-param-key">Flight Altitude</span><span class="drone-param-val">${fp.flight_altitude_meters_above_crop} m above canopy</span></div>
      <div class="drone-param"><span class="drone-param-key">Flight Speed</span><span class="drone-param-val">${fp.flight_speed_m_per_s} m/s</span></div>
      <div class="drone-param"><span class="drone-param-key">Nozzle</span><span class="drone-param-val">Anti-drift 150–250µm</span></div>
    </div>` : ''}

    <!-- Localized text -->
    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">📋</div>
        <div><div class="result-card-title">Field Advisory Card</div></div>
      </div>
      <div class="advisory-lang-toggle">
        <button class="lang-btn active" onclick="switchPestLang('hi',this)">हिंदी</button>
        <button class="lang-btn" onclick="switchPestLang('en',this)">English</button>
      </div>
      <div class="advisory-text" id="pest-advisory-text">${data.localized_advice?.hi || ''}</div>
    </div>
  `;

  window._pestAdvEn = data.localized_advice?.en || '';
  window._pestAdvHi = data.localized_advice?.hi || '';
  el.parentElement.scrollTop = 0;
}

window.switchPestLang = function(lang, btn) {
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('pest-advisory-text').textContent =
    lang === 'hi' ? window._pestAdvHi : window._pestAdvEn;
};

// =============================
// ERROR
// =============================
function renderError(msg) {
  document.getElementById('results-placeholder').style.display = 'none';
  const el = document.getElementById('results-content');
  el.style.display = 'block';
  el.innerHTML = `
    <div class="result-card" style="border-color:#fca5a5;background:#fff1f2">
      <div class="result-card-header">
        <div class="result-card-icon">❌</div>
        <div><div class="result-card-title" style="color:#dc2626">Request Failed</div></div>
      </div>
      <p style="font-size:12px;color:#9f1239">${msg}</p>
      <p style="font-size:11px;color:#64748b;margin-top:8px">If the database is not connected, the server runs in GEE simulation mode. Check <a href="/docs" target="_blank">API Docs</a> for details.</p>
    </div>`;
}
