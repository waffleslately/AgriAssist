// ===== APPLICATION STATE & CONTROLLER =====

let currentFarmer = {
  name: 'Harpreet Singh',
  phone_number: '9876543210',
  state: 'Punjab',
  district: 'Ludhiana',
  village: 'Gill',
  plots: []
};

// Initialize App
document.addEventListener('DOMContentLoaded', async () => {
  const sowDate = new Date();
  sowDate.setDate(sowDate.getDate() - 25);
  const sowInput = document.getElementById('sowing-date');
  if (sowInput) sowInput.value = sowDate.toISOString().split('T')[0];

  const savedPhone = localStorage.getItem('kisan_phone') || '9876543210';
  await loadFarmerSession(savedPhone);

  checkHealth();

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      const target = document.getElementById('tab-' + tab);
      if (target) target.classList.add('active');
    });
  });

  loadSamplePunjabField();
});

// ===== FARMER SESSION & PROFILES =====

async function loadFarmerSession(phone) {
  try {
    const profile = await apiGetFarmerProfile(phone);
    if (profile) currentFarmer = profile;
  } catch (e) {
    console.warn('Profile fetch fallback:', e);
  }

  document.getElementById('user-display-name').textContent = currentFarmer.name;
  document.getElementById('user-display-phone').textContent = '+91 ' + currentFarmer.phone_number;
  document.getElementById('fb-name').textContent = currentFarmer.name;
  document.getElementById('fb-location').textContent = currentFarmer.state + ' · ' + currentFarmer.district + (currentFarmer.village ? ' · ' + currentFarmer.village : '');

  document.getElementById('phone').value = currentFarmer.phone_number;
  document.getElementById('farmer-name').value = currentFarmer.name;
  if (currentFarmer.state) document.getElementById('state').value = currentFarmer.state;
  if (currentFarmer.district) document.getElementById('district').value = currentFarmer.district;
  if (currentFarmer.village) document.getElementById('village').value = currentFarmer.village;

  const select = document.getElementById('saved-plots-select');
  select.innerHTML = '<option value="">-- Select Saved Plot --</option>';
  if (currentFarmer.plots && currentFarmer.plots.length > 0) {
    currentFarmer.plots.forEach((p, idx) => {
      const opt = document.createElement('option');
      opt.value = idx;
      opt.textContent = `${p.plot_name} (${p.crop_name} - ${p.area_acres} ac)`;
      select.appendChild(opt);
    });
  }
}

window.loadSelectedPlot = function(idx) {
  if (idx === '' || !currentFarmer.plots[idx]) return;
  const p = currentFarmer.plots[idx];
  document.getElementById('crop-name').value = p.crop_name || 'wheat';
  if (p.sowing_date) document.getElementById('sowing-date').value = p.sowing_date;
  if (p.centroid) map.setView([p.centroid.lat, p.centroid.lng], 15);
};

// ===== AUTH & OTP MODAL =====

window.openAuthModal = function() {
  document.getElementById('auth-modal').style.display = 'flex';
  document.getElementById('auth-step-1').style.display = 'block';
  document.getElementById('auth-step-2').style.display = 'none';
  document.getElementById('auth-phone').value = currentFarmer.phone_number;
  document.getElementById('auth-name').value = currentFarmer.name;
};

window.closeAuthModal = function() {
  document.getElementById('auth-modal').style.display = 'none';
};

window.resetAuthStep = function() {
  document.getElementById('auth-step-1').style.display = 'block';
  document.getElementById('auth-step-2').style.display = 'none';
};

window.requestVerificationCode = async function() {
  const phone = document.getElementById('auth-phone').value.trim();
  const name = document.getElementById('auth-name').value.trim();
  const state = document.getElementById('auth-state').value;
  const district = document.getElementById('district').value.trim();

  if (phone.length < 10) {
    alert('Please enter a valid 10-digit mobile number.');
    return;
  }

  try {
    const res = await apiRequestOTP(phone, name, state, district);
    document.getElementById('auth-step-1').style.display = 'none';
    document.getElementById('auth-step-2').style.display = 'block';
    document.getElementById('otp-code-display').textContent = res.verification_code;
    document.getElementById('auth-otp-input').value = res.verification_code;
  } catch (e) {
    alert('Failed to request OTP: ' + e.message);
  }
};

window.verifyAndLogin = async function() {
  const phone = document.getElementById('auth-phone').value.trim();
  const otp = document.getElementById('auth-otp-input').value.trim();

  if (!otp) {
    alert('Please enter the 6-digit verification code.');
    return;
  }

  try {
    const res = await apiVerifyOTP(phone, otp);
    if (res.access_token) {
      localStorage.setItem('kisan_token', res.access_token);
      localStorage.setItem('kisan_phone', phone);
      await loadFarmerSession(phone);
      closeAuthModal();
      alert(`Welcome, ${currentFarmer.name}! Your personal farm dashboard is active.`);
    }
  } catch (e) {
    alert('Verification failed: ' + e.message);
  }
};

window.quickLogin = async function(phone, name, state, district) {
  document.getElementById('auth-phone').value = phone;
  document.getElementById('auth-name').value = name;
  document.getElementById('auth-state').value = state;
  await requestVerificationCode();
};

// ===== MANUAL OVERRIDE TOGGLE =====

window.toggleManualOverrides = function(forceVal) {
  const toggle = document.getElementById('manual-override-toggle');
  if (typeof forceVal === 'boolean') {
    toggle.checked = forceVal;
  } else {
    toggle.checked = !toggle.checked;
  }
  const body = document.getElementById('override-body');
  body.style.display = toggle.checked ? 'block' : 'none';
};

// ===== SAMPLE FIELD PRESET =====

function loadSamplePunjabField() {
  const sampleCoords = [
    [75.8500, 30.9000],
    [75.8545, 30.9000],
    [75.8545, 30.9045],
    [75.8500, 30.9045],
    [75.8500, 30.9000]
  ];
  window.setBoundaryCoordinates(sampleCoords);
}

// ===== PLOT ONBOARDING & ADVISORY SUBMISSION =====

document.getElementById('submit-btn').addEventListener('click', async () => {
  if (!window.currentCoords) {
    alert('Please draw your field boundary on the map first.');
    return;
  }

  const isManual = document.getElementById('manual-override-toggle').checked;

  const payload = {
    phone_number: document.getElementById('phone').value.trim(),
    farmer_name:  document.getElementById('farmer-name').value.trim(),
    state:        document.getElementById('state').value,
    district:     document.getElementById('district').value.trim(),
    village:      document.getElementById('village').value.trim() || null,
    language:     document.getElementById('language').value,
    plot_name:    'Main Field (' + document.getElementById('crop-name').value + ')',
    boundary:     { type: 'Polygon', coordinates: [window.currentCoords] },
    crop_name:    document.getElementById('crop-name').value,
    variety:      document.getElementById('variety').value.trim() || null,
    season:       document.getElementById('season').value,
    sowing_date:  document.getElementById('sowing-date').value,
    irrigation_source: document.getElementById('irrigation').value,
    soil_texture: document.getElementById('soil-texture').value,
    manual_override_enabled: isManual,
    manual_soil_n: isManual ? parseFloat(document.getElementById('manual-n').value) : null,
    manual_soil_p: isManual ? parseFloat(document.getElementById('manual-p').value) : null,
    manual_soil_k: isManual ? parseFloat(document.getElementById('manual-k').value) : null,
    manual_soil_ph: isManual ? parseFloat(document.getElementById('manual-ph').value) : null,
    manual_soil_oc: isManual ? parseFloat(document.getElementById('manual-oc').value) : null,
    manual_rain_48h_mm: isManual ? parseFloat(document.getElementById('manual-rain').value) : null
  };

  showLoading('Generating Comprehensive Agricultural Advisory...');
  try {
    const data = await apiOnboardPlot(payload);
    hideLoading();
    renderAdvisoryResults(data, payload.language);
    await loadFarmerSession(payload.phone_number);
  } catch (e) {
    hideLoading();
    renderError(e.message);
  }
});

// ===== DRONE IMAGERY ANALYSIS =====

window.handleDroneFileUpload = function(e) {
  const file = e.target.files[0];
  if (file) {
    const badge = document.getElementById('file-uploaded-badge');
    badge.textContent = `📁 ${file.name} (${(file.size/1024/1024).toFixed(1)} MB)`;
    badge.style.display = 'inline-block';
  }
};

window.applyDronePreset = function(preset) {
  if (preset === 'wheat_vigor') {
    document.getElementById('drone-crop').value = 'wheat';
    document.getElementById('drone-sensor').value = 'multispectral_ndvi';
    document.getElementById('drone-altitude').value = '35';
    document.getElementById('drone-acres').value = '3.8';
  } else if (preset === 'cotton_weed') {
    document.getElementById('drone-crop').value = 'cotton';
    document.getElementById('drone-sensor').value = 'rgb_vari';
    document.getElementById('drone-altitude').value = '25';
    document.getElementById('drone-acres').value = '4.5';
  } else if (preset === 'paddy_lodging') {
    document.getElementById('drone-crop').value = 'paddy';
    document.getElementById('drone-sensor').value = 'multispectral_ndvi';
    document.getElementById('drone-altitude').value = '50';
    document.getElementById('drone-acres').value = '5.0';
  }
};

window.triggerDroneAnalysis = async function() {
  const crop = document.getElementById('drone-crop').value;
  const sensor = document.getElementById('drone-sensor').value;
  const altitude = parseFloat(document.getElementById('drone-altitude').value);
  const acres = parseFloat(document.getElementById('drone-acres').value) || 3.5;

  const payload = {
    crop_name: crop,
    total_area_acres: acres,
    sensor_type: sensor,
    flight_altitude_meters: altitude,
    plot_coordinates: window.currentCoords
  };

  showLoading('Analyzing Aerial Drone Imagery & Canopy Patches...');
  try {
    const data = await apiAnalyzeDroneImage(payload);
    hideLoading();
    if (window.renderDronePatchesOnMap) {
      window.renderDronePatchesOnMap(data.patches);
    }
    renderDroneResults(data);
  } catch (e) {
    hideLoading();
    renderError(e.message);
  }
};

// ===== PEST & IPM DIAGNOSIS =====

window.triggerPestDiagnosis = async function() {
  const crop = document.getElementById('pest-crop').value;
  const pest = document.getElementById('pest-key').value;
  const severity = parseFloat(document.getElementById('severity-slider').value);
  const droneSpray = document.getElementById('drone-spray').checked;

  const payload = {
    plot_id: '00000000-0000-0000-0000-000000000001',
    crop_cycle_id: '00000000-0000-0000-0000-000000000002',
    crop_name: crop,
    pest_key: pest,
    severity_observed_pct: severity,
    drone_spray_requested: droneSpray
  };

  showLoading('Diagnosing Pest & Evaluating CIBRC / DGCA Thresholds...');
  try {
    const data = await apiDiagnosePest(payload);
    hideLoading();
    renderPestResults(data);
  } catch (e) {
    hideLoading();
    renderError(e.message);
  }
};

// ===== RENDERERS =====

function renderAdvisoryResults(data, lang) {
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

  const ndvi = sat.mean_ndvi;
  let ndviStatus = 'Healthy / Vigorous', ndviClass = 'status-green';
  if (ndvi < 0.38) { ndviStatus = 'Stressed / Low Vigor'; ndviClass = 'status-red'; }
  else if (ndvi < 0.55) { ndviStatus = 'Moderate Vigor'; ndviClass = 'status-amber'; }
  const ndviPct = Math.min(100, Math.max(0, ((ndvi + 1) / 2) * 100));

  const fertRows = (rec.fertilizer_schedule || []).map(f => {
    const icons = { Urea: '🟡', DAP: '🟤', MOP: '🔵' };
    const icon = Object.keys(icons).find(k => f.fertilizer.includes(k)) || '🌿';
    return `
    <div class="fert-row">
      <div class="fert-icon">${icons[icon] || '🌿'}</div>
      <div class="fert-info">
        <div class="fert-name">${f.fertilizer}</div>
        <div class="fert-dose">${f.timing_stage}</div>
        <div class="fert-dose" style="color:#64748b;margin-top:2px">${f.instructions.substring(0,80)}...</div>
      </div>
      <div class="fert-bags">
        <div class="fert-bags-val">${f.bags_per_acre}</div>
        <div class="fert-bags-label">bags/acre</div>
        <div class="fert-bags-label">${f.quantity_kg_per_acre} kg/ac</div>
      </div>
    </div>`;
  }).join('');

  const rainWarningCard = rec.weather_warning ? `
    <div class="result-card" style="border-color:#fca5a5;background:#fff1f2">
      <div class="result-card-header">
        <div class="result-card-icon">⚠️</div>
        <div>
          <div class="result-card-title" style="color:#dc2626">Heavy Rain Alert – Hold Fertilizer</div>
          <div class="result-card-sub">${wx.precipitation_48h_mm} mm forecast in next 48 hours</div>
        </div>
      </div>
      <p style="font-size:11.5px;color:#9f1239">
        Heavy precipitation will cause urea volatilization and surface leaching. Hold all top-dressing applications until rain subsides.
      </p>
    </div>` : '';

  el.innerHTML = `
    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">📍</div>
        <div>
          <div class="result-card-title">${plot.name}</div>
          <div class="result-card-sub">${crop.crop_name.toUpperCase()} · ${crop.stage} · Day ${crop.days_after_sowing}</div>
        </div>
      </div>
      <div class="metric-grid">
        <div class="metric-box">
          <div class="metric-val">${plot.area_acres}</div>
          <div class="metric-label">Calculated Acres</div>
        </div>
        <div class="metric-box">
          <div class="metric-val">Day ${crop.days_after_sowing}</div>
          <div class="metric-label">Crop Stage</div>
        </div>
      </div>
    </div>

    ${rainWarningCard}

    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🛰️</div>
        <div>
          <div class="result-card-title">Sentinel-2 Canopy Health</div>
          <div class="result-card-sub">${sat.source || 'Sentinel-2 Harmonized'}</div>
        </div>
      </div>
      <div class="ndvi-bar-wrap">
        <div class="ndvi-bar-bg">
          <div class="ndvi-marker" style="left:${ndviPct}%"></div>
        </div>
        <div class="ndvi-val">${ndvi}</div>
      </div>
      <div style="margin-top:8px;display:flex;justify-content:space-between;align-items:center">
        <span class="status-badge ${ndviClass}">${ndviStatus}</span>
        <span style="font-size:11px;color:#64748b">Moisture Proxy: ${sat.soil_moisture_proxy || '0.38'}</span>
      </div>
    </div>

    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🌍</div>
        <div>
          <div class="result-card-title">Soil Fertility Profile</div>
          <div class="result-card-sub">Source: ${soil.source}</div>
        </div>
      </div>
      <div class="nutrient-grid">
        <div class="nutrient-box ${soil.available_nitrogen_kg_ha < 280 ? 'low' : 'medium'}">
          <div class="nutrient-name">Nitrogen (N)</div>
          <div class="nutrient-status">${soil.available_nitrogen_kg_ha < 280 ? 'LOW' : 'MEDIUM'}</div>
          <div style="font-size:10px;opacity:.8">${soil.available_nitrogen_kg_ha} kg/ha</div>
        </div>
        <div class="nutrient-box ${soil.available_phosphorus_kg_ha < 23 ? 'low' : 'medium'}">
          <div class="nutrient-name">Phosphorus (P)</div>
          <div class="nutrient-status">${soil.available_phosphorus_kg_ha < 23 ? 'LOW' : 'MEDIUM'}</div>
          <div style="font-size:10px;opacity:.8">${soil.available_phosphorus_kg_ha} kg/ha</div>
        </div>
        <div class="nutrient-box ${soil.available_potassium_kg_ha < 140 ? 'low' : 'medium'}">
          <div class="nutrient-name">Potassium (K)</div>
          <div class="nutrient-status">${soil.available_potassium_kg_ha < 140 ? 'LOW' : 'MEDIUM'}</div>
          <div style="font-size:10px;opacity:.8">${soil.available_potassium_kg_ha} kg/ha</div>
        </div>
      </div>
      <div style="margin-top:8px;display:flex;justify-content:space-between;font-size:11px;color:#64748b">
        <span>pH: ${soil.ph}</span>
        <span>Org. Carbon: ${soil.organic_carbon_pct}%</span>
        <span>EC: ${soil.electrical_conductivity || '0.45'} dS/m</span>
      </div>
    </div>

    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🌤️</div>
        <div>
          <div class="result-card-title">Weather Conditions & Forecast</div>
          <div class="result-card-sub">Source: ${wx.source}</div>
        </div>
      </div>
      <div class="weather-row"><span class="weather-key">Daytime Max Temp</span><span class="weather-val">${wx.max_temp}°C</span></div>
      <div class="weather-row"><span class="weather-key">Nighttime Min Temp</span><span class="weather-val">${wx.min_temp}°C</span></div>
      <div class="weather-row">
        <span class="weather-key">Expected 48h Rain</span>
        <span class="weather-val">
          ${wx.precipitation_48h_mm} mm
          ${wx.heavy_rain_warning ? '<span class="status-badge status-red" style="margin-left:4px">⚠️ High</span>' : '<span class="status-badge status-green" style="margin-left:4px">✅ Safe</span>'}
        </span>
      </div>
    </div>

    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🌿</div>
        <div>
          <div class="result-card-title">Fertilizer Prescription (Commercial Bags)</div>
          <div class="result-card-sub">ICAR STCR Aligned · 45kg/50kg Bags</div>
        </div>
      </div>
      ${fertRows || '<p style="font-size:11.5px;color:#64748b">No additional basal or top-dressing chemical fertilizer required at this growth stage.</p>'}
    </div>

    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">📋</div>
        <div>
          <div class="result-card-title">Field Advisory Card</div>
        </div>
      </div>
      <div class="advisory-lang-toggle">
        <button class="lang-btn ${lang==='hi'?'active':''}" onclick="switchAdvisoryLang('hi',this)">हिंदी</button>
        <button class="lang-btn ${lang==='en'?'active':''}" onclick="switchAdvisoryLang('en',this)">English</button>
      </div>
      <div class="advisory-text" id="advisory-text">${localText}</div>
    </div>
  `;

  window._advisoryHi = data.recommendation.localized_hi || localText;
  window._advisoryEn = data.recommendation.localized_en || localText;
  el.parentElement.scrollTop = 0;
}

window.switchAdvisoryLang = function(lang, btn) {
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const txt = lang === 'hi' ? window._advisoryHi : window._advisoryEn;
  document.getElementById('advisory-text').textContent = txt || '';
};

// ===== RENDER DRONE ANALYSIS RESULTS =====

function renderDroneResults(data) {
  document.getElementById('results-placeholder').style.display = 'none';
  const el = document.getElementById('results-content');
  el.style.display = 'block';

  const dgca = data.dgca_precision_mission;
  const counts = {};
  (data.patches || []).forEach(p => {
    counts[p.patch_type] = (counts[p.patch_type] || 0) + 1;
  });

  el.innerHTML = `
    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🚁</div>
        <div>
          <div class="result-card-title">Drone Canopy Analysis Results</div>
          <div class="result-card-sub">${data.sensor_type.replace('_',' ').toUpperCase()} · ${data.flight_altitude_meters}m Altitude</div>
        </div>
      </div>
      <div class="metric-grid">
        <div class="metric-box">
          <div class="metric-val" style="color:#16a34a">${data.overall_stand_uniformity_pct}%</div>
          <div class="metric-label">Canopy Uniformity</div>
        </div>
        <div class="metric-box">
          <div class="metric-val" style="color:#ea580c">${data.stressed_area_pct}%</div>
          <div class="metric-label">Stressed Area</div>
        </div>
      </div>
    </div>

    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🗺️</div>
        <div>
          <div class="result-card-title">Identified Field Zones</div>
          <div class="result-card-sub">Rendered as interactive polygons on the map</div>
        </div>
      </div>
      <div class="metric-grid-4">
        <div class="metric-box">
          <div class="metric-val" style="color:#22c55e;font-size:17px">${counts['healthy_stand'] || 0}</div>
          <div class="metric-label">Healthy Stands</div>
        </div>
        <div class="metric-box">
          <div class="metric-val" style="color:#f97316;font-size:17px">${counts['stressed_crop'] || 0}</div>
          <div class="metric-label">Stressed Patches</div>
        </div>
        <div class="metric-box">
          <div class="metric-val" style="color:#a855f7;font-size:17px">${counts['weed_cluster'] || 0}</div>
          <div class="metric-label">Weed Clusters</div>
        </div>
        <div class="metric-box">
          <div class="metric-val" style="color:#eab308;font-size:17px">${counts['bare_soil_gap'] || 0}</div>
          <div class="metric-label">Bare Soil Gaps</div>
        </div>
      </div>
      <div style="font-size:11px;color:#64748b;margin-top:8px;text-align:center">
        💡 Click any colored patch polygon on the map to inspect its size and treatment.
      </div>
    </div>

    ${dgca ? `
    <div class="result-card" style="border-color:#bae6fd;background:#f0f9ff">
      <div class="result-card-header">
        <div class="result-card-icon">⚡</div>
        <div>
          <div class="result-card-title" style="color:#0369a1">DGCA Precision Drone Spray Mission</div>
          <div class="result-card-sub">Ultra-Low Volume (ULV) Targeted Spot-Spraying</div>
        </div>
      </div>
      <div class="drone-param"><span class="drone-param-key">Target Area</span><span class="drone-param-val">${dgca.target_treatment_area_acres} acres (Stressed Zone)</span></div>
      <div class="drone-param"><span class="drone-param-key">Spray Tank Liquid</span><span class="drone-param-val">${dgca.total_spray_liquid_litres} Litres (${dgca.ulv_water_rate_l_acre} L/acre)</span></div>
      <div class="drone-param"><span class="drone-param-key">Recommended Payload</span><span class="drone-param-val" style="font-size:11px">${dgca.recommended_payload}</span></div>
      <div class="drone-param"><span class="drone-param-key">Flight Speed & Swath</span><span class="drone-param-val">${dgca.flight_speed_m_s} m/s · ${dgca.swath_width_m}m swath</span></div>
      <div class="drone-param"><span class="drone-param-key">Nozzle Specification</span><span class="drone-param-val" style="font-size:11px">${dgca.nozzle_spec}</span></div>
      <div class="drone-param"><span class="drone-param-key">Weather Envelope</span><span class="drone-param-val" style="font-size:10px">${dgca.weather_envelope}</span></div>
    </div>` : ''}

    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">📝</div>
        <div>
          <div class="result-card-title">Zone Management Prescriptions</div>
        </div>
      </div>
      ${(data.management_recommendations || []).map(r => `
        <div style="font-size:11.5px;color:#334155;padding:6px 0;border-bottom:1px solid #f1f5f9;line-height:1.6">
          • ${r}
        </div>
      `).join('')}
    </div>
  `;
  el.parentElement.scrollTop = 0;
}

// ===== RENDER PEST RESULTS =====

function renderPestResults(data) {
  document.getElementById('results-placeholder').style.display = 'none';
  const el = document.getElementById('results-content');
  el.style.display = 'block';

  const etl = data.economic_threshold_breached;
  const dp = data.drone_spray_prescription;
  const fp = dp ? dp.flight_parameters : {};
  const bio = data.ipm_measures ? data.ipm_measures.biological : {};
  const chem = data.ipm_measures ? data.ipm_measures.chemical : {};
  const cultural = data.ipm_measures ? data.ipm_measures.cultural : [];

  el.innerHTML = `
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
          ${etl ? '🚨 ETL Breached (Action Required)' : '✅ Below Economic Threshold'}
        </span>
        <span style="font-size:11.5px;color:#64748b">Severity: ${data.severity_observed_pct}%</span>
      </div>
      <div style="font-size:11px;color:#475569;background:#f8fafc;padding:8px;border-radius:6px;border:1px solid #e2e8f0">
        📌 <strong>CIBRC Standard:</strong> ${data.etl_guideline}
      </div>
    </div>

    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🪤</div>
        <div><div class="result-card-title">Cultural & Mechanical Practices</div></div>
      </div>
      ${cultural.map(m => `<div style="font-size:11.5px;color:#475569;padding:4px 0">• ${m}</div>`).join('')}
    </div>

    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🍃</div>
        <div>
          <div class="result-card-title">Biological Control (Eco-Friendly)</div>
          <div class="result-card-sub">ICAR Approved Bio-pesticides</div>
        </div>
      </div>
      <div class="weather-row"><span class="weather-key">Agent / Product</span><span class="weather-val">${bio.name || '-'}</span></div>
      <div class="weather-row"><span class="weather-key">Recommended Dose</span><span class="weather-val">${bio.dosage_per_acre || '-'}</span></div>
      <div class="weather-row"><span class="weather-key">Application Time</span><span class="weather-val">${bio.timing || '-'}</span></div>
    </div>

    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🧪</div>
        <div>
          <div class="result-card-title">Chemical Treatment (CIBRC Label Claim)</div>
          <div class="result-card-sub">${chem.trade_examples || ''}</div>
        </div>
      </div>
      <div class="weather-row"><span class="weather-key">Active Chemical</span><span class="weather-val" style="font-size:11px">${chem.active_ingredient || '-'}</span></div>
      <div class="weather-row"><span class="weather-key">Knapsack Spray Dose</span><span class="weather-val" style="font-size:11px">${chem.dosage_knapsack_per_acre || '-'}</span></div>
      <div class="weather-row"><span class="weather-key">Pre-Harvest Interval</span><span class="weather-val">${chem.waiting_period_days || '-'} days</span></div>
    </div>

    ${dp && dp.applicable ? `
    <div class="result-card" style="border-color:#bae6fd;background:#f0f9ff">
      <div class="result-card-header">
        <div class="result-card-icon">🚁</div>
        <div>
          <div class="result-card-title" style="color:#0369a1">DGCA Drone Spray Mission SOP</div>
          <div class="result-card-sub">Ultra-Low Volume (ULV) – 10 L/acre</div>
        </div>
      </div>
      <div class="drone-param"><span class="drone-param-key">Spray Water Volume</span><span class="drone-param-val">${dp.drone_water_volume_litres} Litres</span></div>
      <div class="drone-param"><span class="drone-param-key">Chemical Rate</span><span class="drone-param-val">${dp.chemical_rate_per_acre}</span></div>
      <div class="drone-param"><span class="drone-param-key">Flight Altitude</span><span class="drone-param-val">${fp.flight_altitude_meters_above_crop}m above crop canopy</span></div>
      <div class="drone-param"><span class="drone-param-key">Flight Speed</span><span class="drone-param-val">${fp.flight_speed_m_per_s} m/s</span></div>
      <div class="drone-param"><span class="drone-param-key">Nozzle</span><span class="drone-param-val">Anti-drift Flat Fan (150-250µm)</span></div>
    </div>` : ''}

    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">📋</div>
        <div><div class="result-card-title">Localized Farmer Prescription</div></div>
      </div>
      <div class="advisory-lang-toggle">
        <button class="lang-btn active" onclick="switchPestAdvisoryLang('hi',this)">हिंदी</button>
        <button class="lang-btn" onclick="switchPestAdvisoryLang('en',this)">English</button>
      </div>
      <div class="advisory-text" id="pest-advisory-text">${(data.localized_advice && data.localized_advice.hi) || ''}</div>
    </div>
  `;

  window._pestHi = (data.localized_advice && data.localized_advice.hi) || '';
  window._pestEn = (data.localized_advice && data.localized_advice.en) || '';
  el.parentElement.scrollTop = 0;
}

window.switchPestAdvisoryLang = function(lang, btn) {
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('pest-advisory-text').textContent =
    lang === 'hi' ? window._pestHi : window._pestEn;
};

// ===== LOADING & ERROR =====

let loadingInterval;
function showLoading(title) {
  const overlay = document.getElementById('loading-overlay');
  overlay.style.display = 'flex';
  document.getElementById('loading-title').textContent = title || 'Processing Agricultural Intelligence...';
  const steps = ['ls-1','ls-2','ls-3','ls-4','ls-5'];
  steps.forEach(s => document.getElementById(s).classList.remove('active'));
  document.getElementById('ls-1').classList.add('active');
  let i = 1;
  loadingInterval = setInterval(() => {
    if (i < steps.length) {
      document.getElementById(steps[i-1]).classList.remove('active');
      document.getElementById(steps[i]).classList.add('active');
      i++;
    }
  }, 800);
}

function hideLoading() {
  clearInterval(loadingInterval);
  document.getElementById('loading-overlay').style.display = 'none';
}

function renderError(msg) {
  document.getElementById('results-placeholder').style.display = 'none';
  const el = document.getElementById('results-content');
  el.style.display = 'block';
  el.innerHTML = `
    <div class="result-card" style="border-color:#fca5a5;background:#fff1f2">
      <div class="result-card-header">
        <div class="result-card-icon">❌</div>
        <div><div class="result-card-title" style="color:#dc2626">Operation Failed</div></div>
      </div>
      <p style="font-size:12px;color:#9f1239">${msg}</p>
    </div>`;
}
