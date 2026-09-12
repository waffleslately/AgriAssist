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

// ===== MAP MODAL CONTROLS =====

window.openMapModal = function() {
  const overlay = document.getElementById('map-modal-overlay');
  if (overlay) {
    overlay.style.display = 'flex';
    // Fire invalidateSize multiple times to ensure tiles fully render
    [100, 300, 600, 1000].forEach(delay => {
      setTimeout(() => {
        if (window.map) {
          window.map.invalidateSize({ animate: false });
          if (window.currentCoords && window.drawnItems && window.drawnItems.getLayers().length > 0) {
            try { window.map.fitBounds(window.drawnItems.getBounds(), { padding: [40, 40] }); } catch(e) {}
          }
        }
      }, delay);
    });
  }
};

window.closeMapModal = function() {
  const overlay = document.getElementById('map-modal-overlay');
  if (overlay) overlay.style.display = 'none';
};

// Update Land Selectors across tabs
function updateDiagnosisLandSelectors(farmer) {
  const droneSel = document.getElementById('drone-target-land');
  const pestSel = document.getElementById('pest-target-land');
  const plots = (farmer && farmer.plots) ? farmer.plots : [];

  if (droneSel) {
    droneSel.innerHTML = '<option value="">-- Active Form Field --</option>';
    plots.forEach((p, idx) => {
      const opt = document.createElement('option');
      opt.value = idx;
      opt.textContent = `${p.plot_name} (${p.crop_name} - ${p.area_acres} ac)`;
      droneSel.appendChild(opt);
    });
  }

  if (pestSel) {
    pestSel.innerHTML = '<option value="">-- Select One Land to Diagnose --</option>';
    plots.forEach((p, idx) => {
      const opt = document.createElement('option');
      opt.value = idx;
      opt.textContent = `${p.plot_name} (${p.crop_name} - ${p.area_acres} ac)`;
      pestSel.appendChild(opt);
    });
  }
}

window.onDroneLandSelected = function(idx) {
  const hint = document.getElementById('drone-target-land-hint');
  if (idx === '' || !currentFarmer.plots[idx]) {
    if (hint) hint.textContent = 'Using active field coordinates';
    return;
  }
  const p = currentFarmer.plots[idx];
  const cropSel = document.getElementById('drone-crop');
  const acresInput = document.getElementById('drone-acres');
  if (cropSel) cropSel.value = p.crop_name || 'wheat';
  if (acresInput) acresInput.value = p.area_acres || 3.5;
  if (hint) hint.textContent = `Target set to: ${p.plot_name} (${p.crop_name}, ${p.area_acres} ac)`;
};

window.onPestLandSelected = function(idx) {
  const hint = document.getElementById('pest-target-land-hint');
  if (idx === '' || !currentFarmer.plots[idx]) {
    if (hint) hint.textContent = 'Select one specific land to run CIBRC / DGCA diagnosis';
    return;
  }
  const p = currentFarmer.plots[idx];
  const cropSel = document.getElementById('pest-crop');
  if (cropSel) {
    cropSel.value = p.crop_name || 'wheat';
  }
  if (hint) hint.textContent = `Diagnosing: ${p.plot_name} (${p.crop_name}, ${p.stage || 'Active growth'})`;
};

// ── App bootstraps ONLY after Firebase auth gate succeeds ────────────────
// The 'agri-auth-success' event is dispatched by firebaseAuth.js either:
//   (a) immediately, when a valid JWT already exists in localStorage, OR
//   (b) after the user completes Phone OTP verification.
// This ensures NO part of the dashboard is visible before auth.

async function _initAppAfterAuth(detail) {
  const sowDate = new Date();
  sowDate.setDate(sowDate.getDate() - 25);
  const sowInput = document.getElementById('sowing-date');
  if (sowInput) sowInput.value = sowDate.toISOString().split('T')[0];

  const phone = (detail && detail.phone_number)
    || localStorage.getItem('kisan_phone')
    || '9876543210';

  await loadFarmerSession(phone);
  checkHealth();

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      const target = document.getElementById('tab-' + tab);
      if (target) target.classList.add('active');
      if (tab === 'livestock' && window.loadLiveLivestock) {
        window.loadLiveLivestock();
        if (window.startLivestockPolling) window.startLivestockPolling();
      }
    });
  });

  loadSamplePunjabField();
}

window.addEventListener('agri-auth-success', (e) => {
  _initAppAfterAuth(e.detail);
});


// ===== MY FARMS DASHBOARD RENDERER =====

function renderMyFarms(farmer) {
  const listEl = document.getElementById('my-farms-list');
  const countEl = document.getElementById('mf-plot-count');
  const nameEl = document.getElementById('mf-farmer-name');
  const locEl = document.getElementById('mf-farmer-loc');
  if (!listEl) return;

  if (nameEl) nameEl.textContent = farmer.name || 'Farmer Dashboard';
  if (locEl) locEl.textContent = [farmer.state, farmer.district, farmer.village].filter(Boolean).join(' · ');

  const plots = farmer.plots || [];
  if (countEl) countEl.textContent = plots.length + ' Plot' + (plots.length !== 1 ? 's' : '');

  if (!plots.length) {
    listEl.innerHTML = '<div class="mf-empty">No plots saved yet.<br>Complete Plot Onboarding to save your first field.</div>';
    return;
  }

  listEl.innerHTML = plots.map((p, idx) => {
    const ndvi = p.mean_ndvi || 0.55;
    const dotColor = ndvi < 0.38 ? '#ef4444' : ndvi < 0.55 ? '#f59e0b' : '#22c55e';
    const ndviLabel = ndvi < 0.38 ? 'Stressed' : ndvi < 0.55 ? 'Moderate' : 'Healthy';
    const stageLabel = p.stage || '';
    return `
      <div class="mf-plot-card" onclick="loadPlotFromFarms(${idx})" title="Click to load this plot">
        <div class="mf-ndvi-dot" style="background:${dotColor}"></div>
        <div class="mf-plot-info">
          <div class="mf-plot-name">${p.plot_name}</div>
          <div class="mf-plot-meta">${p.crop_name.toUpperCase()} · ${p.area_acres} ac · ${stageLabel}</div>
        </div>
        <div class="mf-plot-ndvi" style="color:${dotColor}">${ndvi.toFixed(2)}<br><span style="font-size:8.5px;font-weight:400">${ndviLabel}</span></div>
      </div>`;
  }).join('');
}

window.loadPlotFromFarms = function(idx) {
  if (!currentFarmer.plots || !currentFarmer.plots[idx]) return;
  const p = currentFarmer.plots[idx];

  // Populate form fields
  const nameInput = document.getElementById('plot-name');
  if (nameInput) nameInput.value = p.plot_name || '';

  const cropSel = document.getElementById('crop-name');
  if (cropSel) cropSel.value = p.crop_name || 'wheat';

  if (p.sowing_date) {
    const d = document.getElementById('sowing-date');
    if (d) d.value = p.sowing_date;
  }

  // Restore boundary on map if stored, else focus centroid
  if (p.coordinates && window.setBoundaryCoordinates) {
    window.setBoundaryCoordinates(p.coordinates);
  } else if (p.centroid && window.map) {
    window.map.setView([p.centroid.lat, p.centroid.lng], 15);
  }

  // Sync the saved-plots dropdown
  const select = document.getElementById('saved-plots-select');
  if (select) select.value = idx;

  // Switch to Plot Onboarding tab
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  const t = document.querySelector('[data-tab="onboard"]');
  if (t) t.classList.add('active');
  const tc = document.getElementById('tab-onboard');
  if (tc) tc.classList.add('active');
};

// ===== ADD NEW PLOT WORKFLOW =====

window.prepareAddNewPlot = function() {
  const nextNum = (currentFarmer.plots ? currentFarmer.plots.length : 0) + 1;
  const nameInput = document.getElementById('plot-name');
  if (nameInput) {
    nameInput.value = `Field ${nextNum}`;
    nameInput.focus();
  }

  // Clear map drawn boundary
  if (window.drawnItems) {
    window.drawnItems.clearLayers();
  }
  window.currentCoords = null;
  if (typeof updateBoundaryStatus === 'function') {
    updateBoundaryStatus(false);
  }

  const submitBtn = document.getElementById('submit-btn');
  if (submitBtn) submitBtn.disabled = true;

  const clearBtn = document.getElementById('clear-btn');
  if (clearBtn) clearBtn.style.display = 'none';

  // Deselect dropdown
  const select = document.getElementById('saved-plots-select');
  if (select) select.value = '';

  // Switch to onboarding tab
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  const t = document.querySelector('[data-tab="onboard"]');
  if (t) t.classList.add('active');
  const tc = document.getElementById('tab-onboard');
  if (tc) tc.classList.add('active');
};


// ===== MULTI-LAND STAGING BATCH STATE =====
let stagedLands = [];

window.stageCurrentPlot = function() {
  if (!window.currentCoords) {
    alert('Please draw the boundary for this land on the map first.');
    return;
  }

  const isManual = document.getElementById('manual-override-toggle').checked;
  const nameInput = document.getElementById('plot-name');
  const cropInput = document.getElementById('crop-name');
  const varietyInput = document.getElementById('variety');
  const seasonInput = document.getElementById('season');
  const sowInput = document.getElementById('sowing-date');
  const irrInput = document.getElementById('irrigation');
  const soilInput = document.getElementById('soil-texture');

  const plotName = (nameInput && nameInput.value.trim()) || (`Field ${stagedLands.length + 1} (${cropInput.value})`);

  const payload = {
    phone_number: document.getElementById('phone').value.trim(),
    farmer_name:  document.getElementById('farmer-name').value.trim(),
    state:        document.getElementById('state').value,
    district:     document.getElementById('district').value.trim(),
    village:      document.getElementById('village').value.trim() || null,
    language:     document.getElementById('language').value,
    plot_name:    plotName,
    boundary:     { type: 'Polygon', coordinates: [window.currentCoords] },
    crop_name:    cropInput.value,
    variety:      varietyInput.value.trim() || null,
    season:       seasonInput.value,
    sowing_date:  sowInput.value,
    irrigation_source: irrInput.value,
    soil_texture: soilInput.value,
    manual_override_enabled: isManual,
    manual_soil_n: isManual ? parseFloat(document.getElementById('manual-n').value) : null,
    manual_soil_p: isManual ? parseFloat(document.getElementById('manual-p').value) : null,
    manual_soil_k: isManual ? parseFloat(document.getElementById('manual-k').value) : null,
    manual_soil_ph: isManual ? parseFloat(document.getElementById('manual-ph').value) : null,
    manual_soil_oc: isManual ? parseFloat(document.getElementById('manual-oc').value) : null,
    manual_rain_48h_mm: isManual ? parseFloat(document.getElementById('manual-rain').value) : null
  };

  stagedLands.push(payload);
  renderStagedLandsQueue();

  // Reset for next field in the batch
  const nextNum = (currentFarmer.plots ? currentFarmer.plots.length : 0) + stagedLands.length + 1;
  if (nameInput) {
    nameInput.value = `Field ${nextNum}`;
    nameInput.focus();
  }

  // Clear map drawn layer
  if (window.drawnItems) window.drawnItems.clearLayers();
  window.currentCoords = null;
  if (typeof updateBoundaryStatus === 'function') updateBoundaryStatus(false);
  const submitBtn = document.getElementById('submit-btn');
  if (submitBtn) submitBtn.disabled = true;
  const stageBtn = document.getElementById('stage-btn');
  if (stageBtn) stageBtn.disabled = true;
  const clearBtn = document.getElementById('clear-btn');
  if (clearBtn) clearBtn.style.display = 'none';

  alert(`Land "${plotName}" added to batch! You can now draw another land on the map or click "Save All Lands at Same Time".`);
};

function renderStagedLandsQueue() {
  const wrap = document.getElementById('staged-queue-wrap');
  const list = document.getElementById('staged-list');
  const count = document.getElementById('staged-count');
  if (!wrap || !list) return;

  if (stagedLands.length === 0) {
    wrap.style.display = 'none';
    return;
  }

  wrap.style.display = 'block';
  if (count) count.textContent = `${stagedLands.length} Land${stagedLands.length > 1 ? 's' : ''}`;

  list.innerHTML = stagedLands.map((item, idx) => `
    <div class="staged-item">
      <div class="staged-item-info">
        <span class="staged-item-name">📍 ${item.plot_name}</span>
        <span class="staged-item-sub">${item.crop_name.toUpperCase()} · ${item.season}</span>
      </div>
      <button type="button" class="staged-item-del" onclick="removeStagedLand(${idx})" title="Remove this land">🗑</button>
    </div>
  `).join('');
}

window.removeStagedLand = function(idx) {
  stagedLands.splice(idx, 1);
  renderStagedLandsQueue();
};

window.saveAllStagedLands = async function() {
  if (stagedLands.length === 0) {
    alert('No lands in batch. Please draw a land and click "Add to Batch" first.');
    return;
  }

  showLoading(`Saving ${stagedLands.length} Lands at the same time...`);
  let lastAdvisoryData = null;
  let savedCount = 0;

  try {
    for (const payload of stagedLands) {
      const data = await apiOnboardPlot(payload);
      lastAdvisoryData = data;
      savedCount++;
    }

    const phone = stagedLands[0].phone_number;
    stagedLands = [];
    renderStagedLandsQueue();

    hideLoading();
    if (lastAdvisoryData) {
      renderAdvisoryResults(lastAdvisoryData, 'hi');
    }
    await loadFarmerSession(phone);
    alert(`Success! All ${savedCount} lands were saved at the same time into your farm profile.`);
  } catch (e) {
    hideLoading();
    renderError('Batch save error: ' + e.message);
  }
};

// ===== FARMER SESSION & PROFILES =====

// ===== FARMER SESSION & PROFILES =====

function updateTopHeaderProfile(farmer) {
  const topName = document.getElementById('top-user-name');
  if (topName) topName.textContent = farmer.name || 'Farmer Account';
  const fbName = document.getElementById('fb-name');
  if (fbName) fbName.textContent = farmer.name || 'Farmer Account';
  const fbLoc = document.getElementById('fb-location');
  if (fbLoc) fbLoc.textContent = (farmer.state || 'Punjab') + ' · ' + (farmer.district || 'Ludhiana') + (farmer.village ? ' · ' + farmer.village : '');
}

async function loadFarmerSession(phone) {
  try {
    const profile = await apiGetFarmerProfile(phone);
    if (profile) currentFarmer = profile;
  } catch (e) {
    console.warn('Profile fetch fallback:', e);
  }

  updateTopHeaderProfile(currentFarmer);

  const udn = document.getElementById('user-display-name');
  if (udn) udn.textContent = currentFarmer.name;
  const udp = document.getElementById('user-display-phone');
  if (udp) udp.textContent = '+91 ' + currentFarmer.phone_number;

  const phoneEl = document.getElementById('phone');
  if (phoneEl) phoneEl.value = currentFarmer.phone_number;
  const farmerNameEl = document.getElementById('farmer-name');
  if (farmerNameEl) farmerNameEl.value = currentFarmer.name;
  if (currentFarmer.state && document.getElementById('state')) document.getElementById('state').value = currentFarmer.state;
  if (currentFarmer.district && document.getElementById('district')) document.getElementById('district').value = currentFarmer.district;
  if (currentFarmer.village && document.getElementById('village')) document.getElementById('village').value = currentFarmer.village;

  renderMyFarms(currentFarmer);
  updateDiagnosisLandSelectors(currentFarmer);
  const select = document.getElementById('saved-plots-select');
  if (select) {
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
}

window.loadSelectedPlot = function(idx) {
  if (idx === '') return;
  loadPlotFromFarms(parseInt(idx));
};

// ===== COMPREHENSIVE USER PROFILE MODAL CONTROLLER =====

window.openUserProfileModal = function() {
  const modal = document.getElementById('user-profile-modal');
  if (!modal) return;

  const f = currentFarmer || { name: 'Harpreet Singh', phone_number: '9876543210', state: 'Punjab', district: 'Ludhiana', village: 'Gill', plots: [] };

  // Identity
  const nameEl = document.getElementById('prof-name');
  if (nameEl) nameEl.textContent = f.name || 'Harpreet Singh';
  const phoneEl = document.getElementById('prof-phone');
  if (phoneEl) phoneEl.textContent = '+91 ' + (f.phone_number || '9876543210');
  const uidEl = document.getElementById('prof-uid');
  if (uidEl) uidEl.textContent = 'UID: KISAN-' + (f.state ? f.state.substring(0,2).toUpperCase() : 'IN') + '-' + (f.phone_number ? f.phone_number.substring(4) : '2026') + ' · Verified Farmer';
  const locEl = document.getElementById('prof-location');
  if (locEl) locEl.textContent = `📍 ${f.state || 'Punjab'} · District ${f.district || 'Ludhiana'} · Village ${f.village || 'Gill'}`;

  // Acreage & plots calculation
  const plots = f.plots || [];
  let totalAcres = 0;
  plots.forEach(p => totalAcres += (parseFloat(p.area_acres) || 0));
  if (totalAcres === 0) totalAcres = 6.3; // Default sample

  const acresEl = document.getElementById('prof-acres');
  if (acresEl) acresEl.textContent = totalAcres.toFixed(1) + ' Ac';
  const plotCountEl = document.getElementById('prof-plot-count');
  if (plotCountEl) plotCountEl.textContent = Math.max(1, plots.length) + ' Plots';

  // Populate registered plots list
  const plotsListEl = document.getElementById('prof-plots-list');
  if (plotsListEl) {
    if (plots.length === 0) {
      plotsListEl.innerHTML = `
        <div style="font-size:11.5px;padding:6px 8px;background:rgba(0,255,136,0.05);border-radius:6px;display:flex;justify-content:space-between">
          <span>🌾 <strong>Field 1 (Main Khet)</strong> · Wheat HD-2967 · 3.8 Ac</span>
          <span style="color:#22c55e;font-weight:700">● NDVI 0.74 (Healthy)</span>
        </div>
        <div style="font-size:11.5px;padding:6px 8px;background:rgba(0,255,136,0.05);border-radius:6px;display:flex;justify-content:space-between">
          <span>🌱 <strong>Field 2 (Canal Side)</strong> · Mustard Pusa-Bold · 2.5 Ac</span>
          <span style="color:#22c55e;font-weight:700">● NDVI 0.68 (Vigorous)</span>
        </div>
      `;
    } else {
      plotsListEl.innerHTML = plots.map((p, i) => `
        <div style="font-size:11.5px;padding:6px 8px;background:rgba(0,255,136,0.05);border-radius:6px;display:flex;justify-content:space-between">
          <span>🌾 <strong>${p.plot_name}</strong> · ${p.crop_name.toUpperCase()} · ${p.area_acres} Ac</span>
          <span style="color:#22c55e;font-weight:700">● NDVI ${(p.mean_ndvi || 0.72).toFixed(2)} (${p.stage || 'Active Growth'})</span>
        </div>
      `).join('');
    }
  }

  // Soil Nutrient Labs
  const nVal = document.getElementById('manual-n') ? document.getElementById('manual-n').value : '190';
  const pVal = document.getElementById('manual-p') ? document.getElementById('manual-p').value : '18';
  const kVal = document.getElementById('manual-k') ? document.getElementById('manual-k').value : '130';
  const phVal = document.getElementById('manual-ph') ? document.getElementById('manual-ph').value : '7.4';
  const ocVal = document.getElementById('manual-oc') ? document.getElementById('manual-oc').value : '0.45';

  const soilN = document.getElementById('prof-soil-n');
  if (soilN) soilN.textContent = `${nVal} kg/ha (Low Deficit <280)`;
  const soilP = document.getElementById('prof-soil-p');
  if (soilP) soilP.textContent = `${pVal} kg/ha (Medium <23)`;
  const soilK = document.getElementById('prof-soil-k');
  if (soilK) soilK.textContent = `${kVal} kg/ha (Low Deficit <140)`;
  const soilPh = document.getElementById('prof-soil-ph');
  if (soilPh) soilPh.textContent = `pH ${phVal} (Optimum) · ${ocVal}% Organic Carbon`;

  modal.style.display = 'flex';
};

window.closeUserProfileModal = function() {
  const modal = document.getElementById('user-profile-modal');
  if (modal) modal.style.display = 'none';
};

// ===== NEW USER REGISTRATION CONTROLLER =====

window.openNewUserModal = function() {
  const modal = document.getElementById('new-user-modal');
  if (modal) modal.style.display = 'flex';
};

window.closeNewUserModal = function() {
  const modal = document.getElementById('new-user-modal');
  if (modal) modal.style.display = 'none';
};

window.registerNewFarmer = async function() {
  const name = document.getElementById('reg-name').value.trim();
  const phone = document.getElementById('reg-phone').value.trim();
  const state = document.getElementById('reg-state').value;
  const district = document.getElementById('reg-district').value.trim();
  const village = document.getElementById('reg-village').value.trim();
  const crop = document.getElementById('reg-crop').value;
  const acres = parseFloat(document.getElementById('reg-acres').value) || 3.5;

  if (!name) {
    alert('Please enter your full name.');
    return;
  }
  if (phone.length < 10) {
    alert('Please enter a valid 10-digit mobile number.');
    return;
  }

  // Create new farmer object
  const newFarmer = {
    name: name,
    phone_number: phone,
    state: state,
    district: district,
    village: village,
    plots: [
      {
        plot_name: 'Field 1 (Main Plot)',
        crop_name: crop,
        variety: 'High-Yield Hybrid',
        area_acres: acres,
        mean_ndvi: 0.65,
        stage: 'Vegetative'
      }
    ]
  };

  currentFarmer = newFarmer;
  localStorage.setItem('kisan_token', 'dev-registered-token-' + Date.now());
  localStorage.setItem('kisan_phone', phone);

  updateTopHeaderProfile(newFarmer);
  await loadFarmerSession(phone);

  closeNewUserModal();
  if (typeof showToast === 'function') {
    showToast(`🎉 Welcome, ${name}! Your new farm account is ready.`);
  } else {
    alert(`Welcome, ${name}! Your farm account is ready.`);
  }
};

// ===== LOGOUT CONTROLLER =====

window.logoutFarmer = function() {
  localStorage.removeItem('kisan_token');
  localStorage.removeItem('kisan_phone');

  closeUserProfileModal();

  if (typeof showToast === 'function') {
    showToast('👋 Logged out successfully. Please sign in or register.');
  }

  // Open the login modal so user can log in or register
  setTimeout(() => {
    openAuthModal();
  }, 400);
};

// ===== AUTH & OTP MODAL =====

window.openAuthModal = function() {
  document.getElementById('auth-modal').style.display = 'flex';
  document.getElementById('auth-step-1').style.display = 'block';
  document.getElementById('auth-step-2').style.display = 'none';
  document.getElementById('auth-phone').value = currentFarmer.phone_number || '9876543210';
  document.getElementById('auth-name').value = currentFarmer.name || 'Harpreet Singh';
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
  const district = document.getElementById('district') ? document.getElementById('district').value.trim() : 'Ludhiana';

  if (phone.length < 10) {
    alert('Please enter a valid 10-digit mobile number.');
    return;
  }

  try {
    const res = await apiRequestOTP(phone, name, state, district);
    document.getElementById('auth-step-1').style.display = 'none';
    document.getElementById('auth-step-2').style.display = 'block';
    document.getElementById('otp-code-display').textContent = res.verification_code || '123456';
    document.getElementById('auth-otp-input').value = res.verification_code || '123456';
  } catch (e) {
    // Fallback in simulation
    document.getElementById('auth-step-1').style.display = 'none';
    document.getElementById('auth-step-2').style.display = 'block';
    document.getElementById('otp-code-display').textContent = '123456';
    document.getElementById('auth-otp-input').value = '123456';
  }
};

window.verifyAndLogin = async function() {
  const phone = document.getElementById('auth-phone').value.trim();
  const otp = document.getElementById('auth-otp-input').value.trim();

  if (!otp) {
    alert('Please enter the 6-digit verification code.');
    return;
  }

  localStorage.setItem('kisan_token', 'token-' + phone);
  localStorage.setItem('kisan_phone', phone);
  await loadFarmerSession(phone);
  closeAuthModal();
  if (typeof showToast === 'function') {
    showToast(`🌾 Welcome back, ${currentFarmer.name}!`);
  } else {
    alert(`Welcome, ${currentFarmer.name}! Your farm dashboard is active.`);
  }
};

window.quickLogin = async function(phone, name, state, district) {
  document.getElementById('auth-phone').value = phone;
  document.getElementById('auth-name').value = name;
  document.getElementById('auth-state').value = state;

  // Direct fast login for presets
  currentFarmer = {
    name: name,
    phone_number: phone,
    state: state,
    district: district,
    village: 'Local Block',
    plots: [
      {
        plot_name: 'Field 1',
        crop_name: state === 'Punjab' ? 'wheat' : (state === 'Maharashtra' ? 'cotton' : 'soybean'),
        variety: 'Regional Certified',
        area_acres: state === 'Punjab' ? 3.8 : 5.0,
        mean_ndvi: 0.71,
        stage: 'Active Growth'
      }
    ]
  };

  localStorage.setItem('kisan_token', 'dev-token-' + phone);
  localStorage.setItem('kisan_phone', phone);

  updateTopHeaderProfile(currentFarmer);
  await loadFarmerSession(phone);
  closeAuthModal();

  if (typeof showToast === 'function') {
    showToast(`🌾 Switched account to ${name} (${state})`);
  }
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
    plot_name:    (document.getElementById('plot-name') && document.getElementById('plot-name').value.trim()) || ('Field ' + (currentFarmer.plots ? currentFarmer.plots.length + 1 : 1) + ' (' + document.getElementById('crop-name').value + ')'),
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

    // Auto-prepare plot name for the next field so farmer can easily add multiple plots
    const nameInput = document.getElementById('plot-name');
    if (nameInput) {
      const nextNum = (currentFarmer.plots ? currentFarmer.plots.length : 0) + 1;
      nameInput.value = `Field ${nextNum}`;
    }
  } catch (e) {
    hideLoading();
    renderError(e.message);
  }
});

// ===== DRONE IMAGERY ANALYSIS =====

window.handleDroneFileUpload = function(e) {
  const file = e.target.files[0];
  if (file) {
    window._selectedDroneFile = file;
    const badge = document.getElementById('file-uploaded-badge');
    badge.textContent = `📷 ${file.name} (${(file.size/1024/1024).toFixed(1)} MB)`;
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
  const altitude = parseFloat(document.getElementById('drone-altitude').value) || 35.0;
  const acres = parseFloat(document.getElementById('drone-acres').value) || 3.5;

  // Check if a specific land is selected
  const landSelect = document.getElementById('drone-target-land');
  let selectedPlotId = null;
  if (landSelect && landSelect.value !== '' && typeof currentFarmer !== 'undefined' && currentFarmer && currentFarmer.plots) {
    const p = currentFarmer.plots[landSelect.value];
    if (p) selectedPlotId = p.plot_id || p.id;
  }

  // Build FormData for multipart file upload
  const formData = new FormData();
  if (window._selectedDroneFile) {
    formData.append('file', window._selectedDroneFile);
  }
  formData.append('sensor_type', sensor);
  formData.append('crop_name', crop);
  formData.append('flight_altitude_meters', altitude);
  formData.append('total_area_acres', acres);
  if (selectedPlotId) {
    formData.append('plot_id', selectedPlotId);
  }
  if (window.currentCoords && window.currentCoords.length >= 3) {
    formData.append('plot_coordinates', JSON.stringify(window.currentCoords));
  }

  showLoading('Analyzing Aerial Drone Imagery & Computing NDVI Grid...');
  try {
    const data = await apiAnalyzeDroneImage(formData);
    window._latestDroneData = data;
    hideLoading();
    if (window.renderDronePatchesOnMap) {
      window.renderDronePatchesOnMap(data);
    }
    renderDroneResults(data);
  } catch (e) {
    hideLoading();
    // Render specific validation error message (e.g. 400 bad request details)
    renderError(e.message);
  }
};


// ===== PHOTO-BASED PEST DIAGNOSIS HANDLERS =====
let selectedPestPhotoFile = null;

window.handlePestPhotoSelected = function(file) {
  if (!file) return;
  selectedPestPhotoFile = file;

  // Show preview
  const previewWrap = document.getElementById('pest-img-preview-wrap');
  const previewImg = document.getElementById('pest-img-preview');
  const filenameTxt = document.getElementById('pest-photo-filename');
  const clearBtn = document.getElementById('pest-clear-photo-btn');
  const dropzoneSub = document.getElementById('pest-dropzone-sub');
  const dropzoneIcon = document.getElementById('pest-dropzone-icon');

  if (previewWrap && previewImg) {
    const reader = new FileReader();
    reader.onload = function(e) {
      previewImg.src = e.target.result;
      previewWrap.style.display = 'block';
      if (filenameTxt) filenameTxt.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      if (clearBtn) clearBtn.style.display = 'block';
      if (dropzoneSub) dropzoneSub.style.display = 'none';
      if (dropzoneIcon) dropzoneIcon.textContent = '📸';
    };
    reader.readAsDataURL(file);
  }

  // Automatically start photo diagnosis
  window.triggerPestPhotoDiagnosis();
};

window.clearPestPhoto = function() {
  selectedPestPhotoFile = null;
  const input = document.getElementById('pest-photo-input');
  if (input) input.value = '';
  const previewWrap = document.getElementById('pest-img-preview-wrap');
  if (previewWrap) previewWrap.style.display = 'none';
  const clearBtn = document.getElementById('pest-clear-photo-btn');
  if (clearBtn) clearBtn.style.display = 'none';
  const banner = document.getElementById('pest-detect-status-banner');
  if (banner) banner.style.display = 'none';
  const candBox = document.getElementById('pest-candidate-matches-box');
  if (candBox) candBox.style.display = 'none';
  const dropzoneSub = document.getElementById('pest-dropzone-sub');
  if (dropzoneSub) dropzoneSub.style.display = 'block';
  const dropzoneIcon = document.getElementById('pest-dropzone-icon');
  if (dropzoneIcon) dropzoneIcon.textContent = '🌿';
  showToast("Photo cleared. Reverted to manual pest card selection.");
};

window.triggerPestPhotoDiagnosis = async function() {
  if (!selectedPestPhotoFile) {
    alert("Please select a photo of the affected crop first.");
    return;
  }

  const crop = document.getElementById('pest-crop').value;
  const pestKey = document.getElementById('pest-key').value;
  const severity = parseFloat(document.getElementById('severity-slider').value);
  const droneSpray = document.getElementById('drone-spray').checked;

  const plotId = (function() {
    const sel = document.getElementById('pest-target-land');
    if (sel && sel.value !== '' && currentFarmer.plots[sel.value]) {
      return currentFarmer.plots[sel.value].plot_id || '00000000-0000-0000-0000-000000000001';
    }
    return '00000000-0000-0000-0000-000000000001';
  })();

  const formData = new FormData();
  formData.append('photo', selectedPestPhotoFile);
  formData.append('plot_id', plotId);
  formData.append('crop_hint', crop);
  formData.append('suspected_pest', pestKey);
  formData.append('severity_observed_pct', severity);
  formData.append('drone_spray_requested', droneSpray);

  // Show status banner
  const banner = document.getElementById('pest-detect-status-banner');
  const title = document.getElementById('pest-detect-title');
  const desc = document.getElementById('pest-detect-desc');
  const badge = document.getElementById('pest-confidence-badge');
  const candBox = document.getElementById('pest-candidate-matches-box');

  if (banner) {
    banner.style.display = 'flex';
    if (title) title.textContent = 'Analyzing Crop Symptoms...';
    if (desc) desc.textContent = 'Running pretrained vision model & matching ICAR countermeasures';
    if (badge) badge.style.display = 'none';
  }
  if (candBox) candBox.style.display = 'none';

  showLoading('Analyzing Crop Photo with Pretrained Vision Models...');

  try {
    const data = await apiAnalyzePestPhoto(formData);
    hideLoading();

    // Update Banner
    if (banner) {
      banner.style.display = 'flex';
      if (title) title.textContent = `Identified: ${data.detected_class} (${data.scientific_name || ''})`;
      if (desc) desc.textContent = data.is_uncertain 
        ? 'Confidence below 60% — please review the candidate options below' 
        : `Verified diagnosis via ${data.detection_source.replace(/_/g, ' ')}`;
      if (badge) {
        badge.style.display = 'inline-block';
        badge.textContent = `${data.confidence_pct}% Match`;
        badge.className = data.is_uncertain ? 'pest-confidence-badge uncertain' : 'pest-confidence-badge';
      }
    }

    // If uncertain, display selectable candidate cards
    if (data.is_uncertain && data.alternate_matches && data.alternate_matches.length > 0) {
      if (candBox) {
        candBox.style.display = 'block';
        const candList = document.getElementById('pest-candidate-matches-list');
        if (candList) {
          candList.innerHTML = data.alternate_matches.map(m => `
            <div class="candidate-match-card" onclick="window.confirmPestCandidate('${m.pest_name}')">
              <div>
                <div style="font-weight:700;font-size:12px;color:var(--ag-text-primary)">${m.pest_name}</div>
                <div style="font-size:10.5px;color:var(--ag-text-muted)">${m.scientific_name} | Crops: ${m.affected_crops.join(', ')}</div>
              </div>
              <div style="display:flex;align-items:center;gap:6px">
                <span style="font-weight:800;font-size:11px;color:#b45309">${m.confidence_pct}%</span>
                <span class="btn-text-sm" style="font-size:10.5px">Select ➜</span>
              </div>
            </div>
          `).join('');
        }
      }
    } else if (candBox) {
      candBox.style.display = 'none';
    }

    // Auto-update severity slider if estimated by model
    if (data.estimated_severity_pct && window.updateSeverityIndicator) {
      const slider = document.getElementById('severity-slider');
      if (slider) {
        slider.value = data.estimated_severity_pct;
        window.updateSeverityIndicator(data.estimated_severity_pct);
      }
    }

    // Render diagnostic results & ICAR countermeasures
    renderPestResults(data);
    showToast(`Diagnosed: ${data.detected_class} (${data.confidence_pct}%)`);

  } catch (e) {
    hideLoading();
    if (banner) banner.style.display = 'none';
    renderError(e.message || "Failed to analyze crop photo.");
  }
};

window.confirmPestCandidate = async function(pestName) {
  showLoading(`Loading ICAR countermeasures for ${pestName}...`);
  try {
    const crop = document.getElementById('pest-crop').value;
    const severity = parseFloat(document.getElementById('severity-slider').value);
    const droneSpray = document.getElementById('drone-spray').checked;
    const data = await apiConfirmPestSelection({
      pest_name: pestName,
      crop_hint: crop,
      severity_observed_pct: severity,
      drone_spray_requested: droneSpray
    });
    hideLoading();
    const candBox = document.getElementById('pest-candidate-matches-box');
    if (candBox) candBox.style.display = 'none';
    const title = document.getElementById('pest-detect-title');
    if (title) title.textContent = `Confirmed Selection: ${pestName}`;
    const badge = document.getElementById('pest-confidence-badge');
    if (badge) {
      badge.textContent = 'Farmer Confirmed';
      badge.className = 'pest-confidence-badge';
    }
    renderPestResults(data);
    showToast(`Confirmed: ${pestName}`);
  } catch (e) {
    hideLoading();
    renderError(e.message);
  }
};


// ===== PEST & IPM DIAGNOSIS =====

window.triggerPestDiagnosis = async function() {
  // If photo is selected, route to photo diagnosis
  if (selectedPestPhotoFile) {
    return window.triggerPestPhotoDiagnosis();
  }
  const crop = document.getElementById('pest-crop').value;
  const pest = document.getElementById('pest-key').value;
  const severity = parseFloat(document.getElementById('severity-slider').value);
  const droneSpray = document.getElementById('drone-spray').checked;

  const payload = {
    plot_id: (function() {
      const sel = document.getElementById('pest-target-land');
      if (sel && sel.value !== '' && currentFarmer.plots[sel.value]) {
        return currentFarmer.plots[sel.value].plot_id || '00000000-0000-0000-0000-000000000001';
      }
      return '00000000-0000-0000-0000-000000000001';
    })(),
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


// ===== NDVI TIMESERIES SVG CHART BUILDER =====

function buildNdviChart(timeseries) {
  if (!timeseries || timeseries.length < 2) return '';
  const W = 300, H = 80, PAD = { t: 8, r: 10, b: 22, l: 32 };
  const innerW = W - PAD.l - PAD.r;
  const innerH = H - PAD.t - PAD.b;
  const ndvis = timeseries.map(d => d.ndvi);
  const dates = timeseries.map(d => d.date);
  const minN = Math.min(...ndvis), maxN = Math.max(...ndvis);
  const range = maxN - minN || 0.1;
  const xStep = innerW / (timeseries.length - 1);
  const toX = i => PAD.l + i * xStep;
  const toY = v => PAD.t + innerH - ((v - minN) / range) * innerH;

  // Build polyline points
  const points = timeseries.map((d, i) => `${toX(i)},${toY(d.ndvi)}`).join(' ');
  // Fill area polygon (close back to bottom)
  const fillPoly = timeseries.map((d, i) => `${toX(i)},${toY(d.ndvi)}`).join(' ')
    + ` ${toX(timeseries.length-1)},${PAD.t + innerH} ${toX(0)},${PAD.t + innerH}`;

  // X-axis date labels (show first and last)
  const firstDate = dates[0] ? dates[0].slice(5) : '';
  const lastDate = dates[dates.length-1] ? dates[dates.length-1].slice(5) : '';

  // Dot elements for each data point
  const dots = timeseries.map((d, i) => {
    const x = toX(i), y = toY(d.ndvi);
    const color = d.ndvi < 0.38 ? '#ef4444' : d.ndvi < 0.55 ? '#f59e0b' : '#22c55e';
    return `<circle cx="${x}" cy="${y}" r="3" fill="${color}" stroke="white" stroke-width="1">
      <title>${d.date}: NDVI ${d.ndvi}</title>
    </circle>`;
  }).join('');

  // Y-axis labels
  const yLabels = [minN, (minN+maxN)/2, maxN].map((v, i) => {
    const y = toY(v);
    return `<text x="${PAD.l - 4}" y="${y + 3}" font-size="7" text-anchor="end" fill="#94a3b8">${v.toFixed(2)}</text>`;
  }).join('');

  return `
  <div style="margin-top:10px">
    <div style="font-size:10px;color:#64748b;margin-bottom:4px">📈 60-Day NDVI Trend (Sentinel-2)</div>
    <svg width="100%" viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" style="overflow:visible">
      <defs>
        <linearGradient id="ndviGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#22c55e" stop-opacity="0.35"/>
          <stop offset="100%" stop-color="#22c55e" stop-opacity="0.03"/>
        </linearGradient>
      </defs>
      <!-- Grid lines -->
      <line x1="${PAD.l}" y1="${PAD.t}" x2="${PAD.l}" y2="${PAD.t+innerH}" stroke="#e2e8f0" stroke-width="1"/>
      <line x1="${PAD.l}" y1="${PAD.t+innerH}" x2="${PAD.l+innerW}" y2="${PAD.t+innerH}" stroke="#e2e8f0" stroke-width="1"/>
      <line x1="${PAD.l}" y1="${PAD.t+innerH/2}" x2="${PAD.l+innerW}" y2="${PAD.t+innerH/2}" stroke="#f1f5f9" stroke-width="1" stroke-dasharray="3,2"/>
      <!-- Fill area -->
      <polygon points="${fillPoly}" fill="url(#ndviGrad)"/>
      <!-- Line -->
      <polyline points="${points}" fill="none" stroke="#16a34a" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>
      <!-- Dots -->
      ${dots}
      <!-- Y labels -->
      ${yLabels}
      <!-- X labels -->
      <text x="${PAD.l}" y="${H - 2}" font-size="7" fill="#94a3b8">${firstDate}</text>
      <text x="${PAD.l+innerW}" y="${H - 2}" font-size="7" text-anchor="end" fill="#94a3b8">${lastDate}</text>
    </svg>
  </div>`;
}

// ===== 7-DAY WEATHER FORECAST STRIP BUILDER =====

function buildWeatherStrip(wx) {
  const dates = wx.forecast_dates || [];
  const precip = wx.forecast_precip_mm || [];
  const maxT = wx.forecast_max_temp || [];
  const minT = wx.forecast_min_temp || [];
  if (!dates.length) return '';

  const dayNames = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  const cols = dates.slice(0, 7).map((d, i) => {
    const dt = new Date(d);
    const day = dayNames[dt.getDay()];
    const rain = (precip[i] || 0).toFixed(1);
    const hi = (maxT[i] || '--');
    const lo = (minT[i] || '--');
    const isRainy = (precip[i] || 0) > 5;
    const icon = isRainy ? '🌧️' : (precip[i] > 1 ? '🌦️' : '☀️');
    const rainColor = isRainy ? '#3b82f6' : '#94a3b8';
    return `<div style="flex:1;text-align:center;font-size:9.5px;padding:4px 2px">
      <div style="color:#64748b;font-weight:600">${day}</div>
      <div style="font-size:13px;margin:2px 0">${icon}</div>
      <div style="color:#1e293b;font-weight:600">${typeof hi === 'number' ? Math.round(hi) : hi}°</div>
      <div style="color:#64748b">${typeof lo === 'number' ? Math.round(lo) : lo}°</div>
      <div style="color:${rainColor};font-size:8.5px">${rain}mm</div>
    </div>`;
  }).join('');

  return `
  <div style="margin-top:8px;border-top:1px solid #f1f5f9;padding-top:8px">
    <div style="font-size:10px;color:#64748b;margin-bottom:6px">📅 7-Day Outlook</div>
    <div style="display:flex;gap:2px">${cols}</div>
  </div>`;
}

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
      ${buildNdviChart(sat.ndvi_timeseries)}
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
      ${buildWeatherStrip(wx)}
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
        <button class="lang-btn ${lang==='pa'?'active':''}" onclick="switchAdvisoryLang('pa',this)">ਪੰਜਾਬੀ</button>
        <button class="lang-btn ${lang==='mr'?'active':''}" onclick="switchAdvisoryLang('mr',this)">मराठी</button>
      </div>
      <div class="advisory-text" id="advisory-text">${localText}</div>
      <div style="display:flex;gap:6px;margin-top:10px">
        <button class="btn btn-primary" style="flex:1" onclick="printAdvisorySlip()"><span class="btn-icon">🖨️</span> Print / Save Slip</button>
        <button class="btn" style="flex:1;background:#25d366;color:#fff" onclick="shareAdvisoryWhatsApp()"><span class="btn-icon">💬</span> WhatsApp</button>
      </div>
    </div>
  `;

  window._advisoryHi = data.recommendation.localized_hi || localText;
  window._advisoryEn = data.recommendation.localized_en || localText;
  window._advisoryPa = data.recommendation.localized_pa || localText;
  window._advisoryMr = data.recommendation.localized_mr || localText;
  el.parentElement.scrollTop = 0;
}

window.switchAdvisoryLang = function(lang, btn) {
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const mapping = { hi: window._advisoryHi, en: window._advisoryEn, pa: window._advisoryPa, mr: window._advisoryMr };
  document.getElementById('advisory-text').textContent = mapping[lang] || window._advisoryHi || '';
};

// ===== RENDER DRONE ANALYSIS RESULTS =====

function renderDroneResults(data) {
  document.getElementById('results-placeholder').style.display = 'none';
  const el = document.getElementById('results-content');
  el.style.display = 'block';

  const dgca = data.dgca_precision_mission;
  const counts = {};
  if (data.grid) {
    counts['healthy_stand'] = (data.grid.healthy || []).length;
    counts['moderate_vigor'] = (data.grid.moderate || []).length;
    counts['stressed_crop'] = (data.grid.stressed_or_bare || []).length;
    counts['weed_cluster'] = (data.grid.weed_cluster || []).length;
  } else {
    (data.patches || []).forEach(p => {
      counts[p.patch_type] = (counts[p.patch_type] || 0) + 1;
    });
  }

  el.innerHTML = `
    <!-- PART A: INTERACTIVE DRONE IMAGE & PATCH OVERLAY -->
    <div id="drone-image-overlay-card"></div>

    <!-- PART B: CROP DEVELOPMENT OVER TIME (HISTORICAL TREND CHART) -->
    <div id="drone-history-card"></div>

    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🚁</div>
        <div>
          <div class="result-card-title">Drone Canopy Performance Metrics</div>
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
        <div class="result-card-icon">📊</div>
        <div>
          <div class="result-card-title">Field Zone Breakdown</div>
          <div class="result-card-sub">Classified spatial zones across surveyed plot</div>
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
      <button class="btn btn-drone btn-full" onclick="downloadDroneMissionGeoJSON()" style="margin-top:10px"><span class="btn-icon">📥</span> Download DGCA Flight Plan (GeoJSON)</button>
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

  // Render Part A (Image Overlay) and Part B (Crop Development History)
  if (window.renderDroneOverlayAndHistory) {
    window.renderDroneOverlayAndHistory(data);
  }

  el.parentElement.scrollTop = 0;
}

// ===== RENDER PEST RESULTS =====

function renderPestResults(data) {
  document.getElementById('results-placeholder').style.display = 'none';
  const el = document.getElementById('results-content');
  el.style.display = 'block';

  const pestName = data.pest_name || data.detected_class || 'Crop Pest / Disease';
  const sciName = data.scientific_name || '';
  const severity = data.severity_observed_pct !== undefined ? data.severity_observed_pct : (data.estimated_severity_pct || 18);
  const etl = data.economic_threshold_breached !== undefined ? data.economic_threshold_breached : (severity >= 10);
  const dp = data.drone_prescription || data.drone_spray_prescription;
  const fp = dp ? (dp.flight_parameters || {}) : {};
  const cm = data.countermeasures || {};
  const regNote = data.regulatory_note || (cm.regulatory_note || null);

  const organicList = cm.organic_countermeasures || (data.ipm_measures ? data.ipm_measures.cultural : []);
  const chemList = cm.chemical_countermeasures || [];
  const bio = data.ipm_measures ? data.ipm_measures.biological : {};
  const chem = data.ipm_measures ? data.ipm_measures.chemical : {};
  const symptoms = cm.symptoms || '';
  const idealTiming = cm.ideal_spray_timing || '';
  const sourceNote = cm.source_note || '';

  el.innerHTML = `
    <!-- Top Result Header -->
    <div class="result-card" style="${etl ? 'border-color:#fca5a5;background:rgba(254,226,226,0.2)' : ''}">
      <div class="result-card-header">
        <div class="result-card-icon">🔬</div>
        <div>
          <div class="result-card-title">${pestName}</div>
          <div class="result-card-sub" style="font-style:italic">${sciName}</div>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap">
        <span class="status-badge ${etl ? 'status-red' : 'status-green'}">
          ${etl ? '🚨 ETL Breached (Action Required)' : '✅ Below Critical Threshold'}
        </span>
        <span style="font-size:11.5px;color:var(--ag-text-muted)">Infestation Severity: <strong>${severity}%</strong></span>
        ${data.confidence_pct ? `<span class="pest-confidence-badge ${data.is_uncertain ? 'uncertain' : ''}">${data.confidence_pct}% Match</span>` : ''}
      </div>
      ${symptoms ? `
      <div style="font-size:11px;color:var(--ag-text-primary);background:var(--ag-surface);padding:8px 10px;border-radius:6px;border:1px solid var(--ag-border);line-height:1.4">
        🔍 <strong>Observed Symptoms:</strong> ${symptoms}
      </div>` : ''}
    </div>

    <!-- MANDATORY REGULATORY NOTICE (Rice Blast export restriction flag) -->
    ${regNote ? `
    <div class="pest-regulatory-banner">
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">
        <span style="font-size:16px">⚠️</span>
        <strong style="font-size:12px;text-transform:uppercase;letter-spacing:0.5px">Official Regulatory & Export Warning</strong>
      </div>
      <div>${regNote}</div>
    </div>` : ''}

    <!-- Organic & Biological Countermeasures -->
    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🌿</div>
        <div>
          <div class="result-card-title">Organic & Biological Countermeasures</div>
          <div class="result-card-sub">ICAR Approved Cultural, Mechanical & Bio-Controls</div>
        </div>
      </div>
      ${organicList.length > 0 ? organicList.map(m => `
        <div style="font-size:11.5px;color:var(--ag-text-primary);padding:4px 0;line-height:1.4">• ${m}</div>
      `).join('') : `
        <div class="weather-row"><span class="weather-key">Bio-Agent</span><span class="weather-val">${bio.name || 'Neem Extract 5%'}</span></div>
        <div class="weather-row"><span class="weather-key">Dosage</span><span class="weather-val">${bio.dosage_per_acre || '1000 ml/acre'}</span></div>
      `}
    </div>

    <!-- Chemical Countermeasures -->
    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-icon">🧪</div>
        <div>
          <div class="result-card-title">Chemical Countermeasures</div>
          <div class="result-card-sub">CIBRC & ICAR Verified Chemical Treatments</div>
        </div>
      </div>
      ${chemList.length > 0 ? chemList.map(c => `
        <div style="font-size:11.5px;color:var(--ag-text-primary);padding:4px 0;line-height:1.4">• ${c}</div>
      `).join('') : `
        <div class="weather-row"><span class="weather-key">Active Chemical</span><span class="weather-val">${chem.active_ingredient || '-'}</span></div>
        <div class="weather-row"><span class="weather-key">Knapsack Dose</span><span class="weather-val">${chem.dosage_knapsack_per_acre || '-'}</span></div>
      `}
      ${idealTiming ? `
      <div style="margin-top:8px;font-size:11px;color:#0369a1;background:#f0f9ff;padding:6px 10px;border-radius:4px;border-left:3px solid #0284c7">
        ⏱️ <strong>Ideal Spray Timing:</strong> ${idealTiming}
      </div>` : ''}
    </div>

    <!-- DGCA Ultra-Low Volume Drone Prescription -->
    ${dp && dp.applicable ? `
    <div class="result-card" style="border-color:#bae6fd;background:rgba(240,249,255,0.4)">
      <div class="result-card-header">
        <div class="result-card-icon">🚁</div>
        <div>
          <div class="result-card-title" style="color:#0369a1">DGCA Drone Spray Mission SOP</div>
          <div class="result-card-sub">Ultra-Low Volume (ULV) – 10 L/acre</div>
        </div>
      </div>
      <div class="drone-param"><span class="drone-param-key">Target Chemical Formulation</span><span class="drone-param-val" style="font-size:11px">${dp.target_chemical}</span></div>
      <div class="drone-param"><span class="drone-param-key">Spray Water Volume</span><span class="drone-param-val">${dp.drone_water_volume_litres} Litres (ULV)</span></div>
      <div class="drone-param"><span class="drone-param-key">Application Rate</span><span class="drone-param-val">${dp.chemical_rate_per_acre || 'Standard ICAR rate'}</span></div>
      <div class="drone-param"><span class="drone-param-key">Flight Altitude</span><span class="drone-param-val">${fp.flight_altitude_meters_above_crop || '2.0'}m above crop canopy</span></div>
      <div class="drone-param"><span class="drone-param-key">Flight Speed</span><span class="drone-param-val">${fp.flight_speed_m_per_s || '4.0'} m/s</span></div>
      <div class="drone-param"><span class="drone-param-key">Nozzle Spec</span><span class="drone-param-val">Anti-drift Centrifugal (150-250µm)</span></div>
    </div>` : ''}

    <!-- Official ICAR Research Source Note -->
    ${sourceNote ? `
    <div style="font-size:10px;color:var(--ag-text-muted);margin-top:6px;padding:6px 8px;border-top:1px dashed var(--ag-border);text-align:right">
      🏛️ Source: ${sourceNote}
    </div>` : ''}
  `;

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

// ===== EXPORT & PRINT UTILITIES =====

window.printAdvisorySlip = function() {
  window.print();
};

window.shareAdvisoryWhatsApp = function() {
  const text = encodeURIComponent("🌾 AgriAssist Advisory Prescription:\n" + (document.getElementById('advisory-text') ? document.getElementById('advisory-text').textContent : ''));
  window.open("https://api.whatsapp.com/send?text=" + text, "_blank");
};

window.downloadDroneMissionGeoJSON = function() {
  if (!window._latestDroneData) {
    alert("Please run a drone canopy analysis first.");
    return;
  }
  const geojson = {
    type: "FeatureCollection",
    properties: {
      survey_id: window._latestDroneData.survey_id,
      crop: window._latestDroneData.crop_name,
      sensor: window._latestDroneData.sensor_type,
      dgca_mission: window._latestDroneData.dgca_precision_mission
    },
    features: (window._latestDroneData.patches || []).map(p => ({
      type: "Feature",
      geometry: p.geojson_geometry,
      properties: {
        patch_id: p.patch_id,
        patch_type: p.patch_type,
        severity: p.severity_level,
        area_acres: p.area_acres,
        notes: p.notes
      }
    }))
  };
  const blob = new Blob([JSON.stringify(geojson, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `dgca_drone_mission_${window._latestDroneData.crop_name}_${Date.now()}.geojson`;
  a.click();
  URL.revokeObjectURL(url);
};

// ===== SMART SOIL REPORT INGESTION & RECOMMENDATION =====

let currentSoilReportId = null;
let currentSoilReportData = null;

window.toggleSoilTextInput = function() {
  const box = document.getElementById('soil-text-box');
  const btn = document.getElementById('soil-toggle-text-btn');
  const dropzone = document.getElementById('soil-dropzone');
  if (!box) return;
  if (box.style.display === 'none' || box.style.display === '') {
    box.style.display = 'block';
    if (dropzone) dropzone.style.display = 'none';
    if (btn) btn.textContent = '📁 Upload File';
  } else {
    box.style.display = 'none';
    if (dropzone) dropzone.style.display = 'block';
    if (btn) btn.textContent = '✏️ Paste Text';
  }
};

window.handleSoilFileUpload = async function(file) {
  if (!file) return;
  const feedback = document.getElementById('soil-parse-feedback');
  const title = document.getElementById('soil-parse-title');
  const desc = document.getElementById('soil-parse-desc');
  const icon = document.getElementById('soil-parse-icon');
  const badge = document.getElementById('soil-parse-badge');

  if (feedback) {
    feedback.style.display = 'flex';
    feedback.style.background = '#eff6ff';
    feedback.style.borderColor = '#bfdbfe';
    feedback.style.color = '#1e40af';
  }
  if (icon) icon.textContent = '⏳';
  if (title) title.textContent = `Analyzing ${file.name}...`;
  if (desc) desc.textContent = 'Extracting N, P, K, pH, OC values & standardizing units...';
  if (badge) badge.style.display = 'none';

  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('farmer_id', (typeof currentFarmer !== 'undefined' && currentFarmer && currentFarmer.farmer_id) || 'farmer_1');

    const result = await apiUploadSoilReport(formData);
    currentSoilReportId = result.report_id;
    currentSoilReportData = result.extracted_data;

    // Show success
    if (feedback) {
      feedback.style.background = '#f0fdf4';
      feedback.style.borderColor = '#bbf7d0';
      feedback.style.color = '#166534';
    }
    if (icon) icon.textContent = '✅';
    if (title) title.textContent = `Extracted from ${file.name}`;
    if (desc) {
      const conf = Math.round((result.extracted_data.extraction_confidence || 0.9) * 100);
      desc.textContent = `Format: ${(result.extracted_data.source_format || 'FILE').toUpperCase()} • Confidence: ${conf}%`;
    }
    if (badge) {
      badge.style.display = 'inline-block';
      const conf = Math.round((result.extracted_data.extraction_confidence || 0.9) * 100);
      badge.textContent = `${conf}% Confidence`;
    }

    populateSoilFieldsFromReport(result.extracted_data);
    if (typeof showToast === 'function') {
      showToast(`📄 Soil Report Analyzed: Values populated to manual fields!`);
    }
  } catch (err) {
    if (feedback) {
      feedback.style.background = '#fef2f2';
      feedback.style.borderColor = '#fecaca';
      feedback.style.color = '#991b1b';
    }
    if (icon) icon.textContent = '⚠️';
    if (title) title.textContent = 'Extraction Failed';
    if (desc) desc.textContent = err.message || 'Could not parse report format. You can enter values manually below.';
  }
};

window.handleSoilTextSubmit = async function() {
  const textInput = document.getElementById('soil-raw-text');
  const rawText = textInput ? textInput.value.trim() : '';
  if (!rawText) {
    alert('Please paste or type soil report test results first.');
    return;
  }

  const feedback = document.getElementById('soil-parse-feedback');
  const title = document.getElementById('soil-parse-title');
  const desc = document.getElementById('soil-parse-desc');
  const icon = document.getElementById('soil-parse-icon');
  const badge = document.getElementById('soil-parse-badge');

  if (feedback) {
    feedback.style.display = 'flex';
    feedback.style.background = '#eff6ff';
    feedback.style.borderColor = '#bfdbfe';
    feedback.style.color = '#1e40af';
  }
  if (icon) icon.textContent = '⏳';
  if (title) title.textContent = 'Parsing typed text...';
  if (desc) desc.textContent = 'Extracting NPK and soil metrics via regex matching...';
  if (badge) badge.style.display = 'none';

  try {
    const formData = new FormData();
    formData.append('raw_text', rawText);
    formData.append('farmer_id', (typeof currentFarmer !== 'undefined' && currentFarmer && currentFarmer.farmer_id) || 'farmer_1');

    const result = await apiUploadSoilReport(formData);
    currentSoilReportId = result.report_id;
    currentSoilReportData = result.extracted_data;

    if (feedback) {
      feedback.style.background = '#f0fdf4';
      feedback.style.borderColor = '#bbf7d0';
      feedback.style.color = '#166534';
    }
    if (icon) icon.textContent = '✅';
    if (title) title.textContent = 'Nutrients Extracted from Text';
    const conf = Math.round((result.extracted_data.extraction_confidence || 0.85) * 100);
    if (desc) desc.textContent = `Extracted metrics with ${conf}% confidence`;
    if (badge) {
      badge.style.display = 'inline-block';
      badge.textContent = `${conf}% Match`;
    }

    populateSoilFieldsFromReport(result.extracted_data);
    if (typeof showToast === 'function') {
      showToast('📄 Extracted nutrients from text!');
    }
  } catch (err) {
    if (feedback) {
      feedback.style.background = '#fef2f2';
      feedback.style.borderColor = '#fecaca';
      feedback.style.color = '#991b1b';
    }
    if (icon) icon.textContent = '⚠️';
    if (title) title.textContent = 'Extraction Failed';
    if (desc) desc.textContent = err.message || 'Could not parse text.';
  }
};

function populateSoilFieldsFromReport(ext) {
  if (!ext) return;

  // Auto-enable manual overrides toggle so farmer sees the numbers
  window.toggleManualOverrides(true);

  // Clear previous review highlights
  const fieldIds = ['manual-n', 'manual-p', 'manual-k', 'manual-ph', 'manual-oc', 'manual-ec'];
  fieldIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.classList.remove('field-needs-review');
      // Add event listener to remove review highlight once farmer interacts/edits
      el.oninput = () => el.classList.remove('field-needs-review');
    }
  });

  const reviewNotice = document.getElementById('soil-review-notice');
  let hasReviewFields = false;

  const reviewList = ext.fields_requiring_review || [];

  // Populate N
  const nEl = document.getElementById('manual-n');
  if (nEl && ext.nitrogen_kg_ha != null) {
    nEl.value = Math.round(ext.nitrogen_kg_ha * 10) / 10;
    if (reviewList.includes('nitrogen') || ext.nitrogen_kg_ha <= 0) {
      nEl.classList.add('field-needs-review');
      hasReviewFields = true;
    }
  }

  // Populate P
  const pEl = document.getElementById('manual-p');
  if (pEl && ext.phosphorus_kg_ha != null) {
    pEl.value = Math.round(ext.phosphorus_kg_ha * 10) / 10;
    if (reviewList.includes('phosphorus') || ext.phosphorus_kg_ha <= 0) {
      pEl.classList.add('field-needs-review');
      hasReviewFields = true;
    }
  }

  // Populate K
  const kEl = document.getElementById('manual-k');
  if (kEl && ext.potassium_kg_ha != null) {
    kEl.value = Math.round(ext.potassium_kg_ha * 10) / 10;
    if (reviewList.includes('potassium') || ext.potassium_kg_ha <= 0) {
      kEl.classList.add('field-needs-review');
      hasReviewFields = true;
    }
  }

  // Populate pH
  const phEl = document.getElementById('manual-ph');
  if (phEl && ext.ph != null) {
    phEl.value = Math.round(ext.ph * 100) / 100;
    if (reviewList.includes('ph') || ext.ph < 3.5 || ext.ph > 10.5) {
      phEl.classList.add('field-needs-review');
      hasReviewFields = true;
    }
  }

  // Populate OC
  const ocEl = document.getElementById('manual-oc');
  if (ocEl && ext.organic_carbon_pct != null) {
    ocEl.value = Math.round(ext.organic_carbon_pct * 100) / 100;
    if (reviewList.includes('organic_carbon')) {
      ocEl.classList.add('field-needs-review');
      hasReviewFields = true;
    }
  }

  // Populate EC
  const ecEl = document.getElementById('manual-ec');
  if (ecEl && ext.electrical_conductivity_ds_m != null) {
    ecEl.value = Math.round(ext.electrical_conductivity_ds_m * 100) / 100;
  }

  if (reviewNotice) {
    reviewNotice.style.display = hasReviewFields || ext.needs_manual_review ? 'block' : 'none';
  }

  // Ensure action section is visible
  const actionsCard = document.getElementById('soil-actions-card');
  if (actionsCard) actionsCard.style.display = 'block';
}

async function confirmCurrentSoilValues() {
  if (!currentSoilReportId) {
    currentSoilReportId = 'rep_' + Date.now();
  }
  const payload = {
    nitrogen_kg_ha: parseFloat(document.getElementById('manual-n')?.value) || 190.0,
    phosphorus_kg_ha: parseFloat(document.getElementById('manual-p')?.value) || 18.0,
    potassium_kg_ha: parseFloat(document.getElementById('manual-k')?.value) || 130.0,
    ph: parseFloat(document.getElementById('manual-ph')?.value) || 7.4,
    organic_carbon_pct: parseFloat(document.getElementById('manual-oc')?.value) || 0.45,
    electrical_conductivity: parseFloat(document.getElementById('manual-ec')?.value) || 0.8,
    state: document.getElementById('state')?.value || 'Punjab',
    district: document.getElementById('district')?.value || 'Ludhiana'
  };

  try {
    await apiConfirmSoilReport(currentSoilReportId, payload);
  } catch (e) {
    console.warn('Soil confirm sync note:', e);
  }
  return payload;
}

window.toggleNutrientPlanSection = function() {
  const drawer = document.getElementById('nutrient-calc-drawer');
  if (!drawer) return;
  drawer.style.display = (drawer.style.display === 'none' || drawer.style.display === '') ? 'block' : 'none';
  if (drawer.style.display === 'block') {
    drawer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
};

window.triggerCropSuggestions = async function() {
  const resultsContainer = document.getElementById('soil-action-results');
  if (resultsContainer) {
    resultsContainer.style.display = 'block';
    resultsContainer.innerHTML = `
      <div style="text-align:center;padding:16px;background:var(--ag-surface);border:1px solid var(--ag-border);border-radius:8px">
        <div style="font-size:24px;margin-bottom:6px">🌱</div>
        <div style="font-weight:600;font-size:12px;color:var(--ag-text-primary)">Analyzing Atharva Ingle's Kaggle Reference Dataset...</div>
        <div style="font-size:11px;color:var(--ag-text-muted);margin-top:2px">Evaluating 22 crops against soil NPK, pH, and local weather...</div>
      </div>
    `;
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  try {
    await confirmCurrentSoilValues();
    const lat = (window.currentCoords && window.currentCoords[0] && window.currentCoords[0][1]) || 30.90;
    const lng = (window.currentCoords && window.currentCoords[0] && window.currentCoords[0][0]) || 75.85;

    const data = await apiSuggestCrops(currentSoilReportId, lat, lng);
    renderCropSuggestions(data);
  } catch (err) {
    if (resultsContainer) {
      resultsContainer.innerHTML = `
        <div style="padding:12px;border-radius:8px;background:#fef2f2;border:1px solid #fecaca;color:#991b1b;font-size:12px">
          ⚠️ <strong>Recommendation Error:</strong> ${err.message || 'Could not fetch crop suggestions.'}
        </div>
      `;
    }
  }
};

function renderCropSuggestions(data) {
  const resultsContainer = document.getElementById('soil-action-results');
  if (!resultsContainer || !data.suggested_crops) return;

  const crops = data.suggested_crops;
  const soil = data.input_soil || {};

  let html = `
    <div style="background:var(--ag-surface);border:1px solid var(--ag-border);border-radius:10px;padding:12px;box-shadow:0 2px 6px rgba(0,0,0,0.05)">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;border-bottom:1px solid var(--ag-border);padding-bottom:8px">
        <div>
          <div style="font-weight:700;font-size:13px;color:var(--ag-text-primary)">🌾 Top 5 Recommended Crops For Your Soil</div>
          <div style="font-size:10.5px;color:var(--ag-text-muted)">Based on N: ${soil.nitrogen_kg_ha} • P: ${soil.phosphorus_kg_ha} • K: ${soil.potassium_kg_ha} • pH: ${soil.ph}</div>
        </div>
        <span style="font-size:10px;padding:2px 6px;border-radius:4px;background:rgba(45,106,79,0.1);color:var(--ag-primary);font-weight:700">Kaggle Dataset Match</span>
      </div>
      <div class="crop-rec-grid">
  `;

  crops.forEach((c, idx) => {
    const badgeColor = c.fit_score >= 80 ? '#15803d' : (c.fit_score >= 65 ? '#0284c7' : '#b45309');
    const badgeBg = c.fit_score >= 80 ? '#dcfce7' : (c.fit_score >= 65 ? '#e0f2fe' : '#fef3c7');

    html += `
      <div class="crop-rec-card">
        <div style="display:flex;align-items:center;gap:10px;flex:1">
          <div class="crop-rec-rank">#${idx + 1}</div>
          <div style="flex:1">
            <div style="display:flex;align-items:center;gap:6px">
              <span style="font-weight:700;font-size:13px;color:var(--ag-text-primary)">${c.display_name || c.crop}</span>
              <span style="font-size:10.5px;color:var(--ag-text-muted)">(${c.season || 'Annual'})</span>
            </div>
            <div style="font-size:11px;color:var(--ag-text-muted);margin-top:2px;line-height:1.3">${c.why_suitable || c.suitability_summary}</div>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px">
          <div class="crop-rec-fit" style="color:${badgeColor};background:${badgeBg}">
            ${c.fit_score}% Match
          </div>
          <button type="button" class="btn btn-sm btn-primary" onclick="selectCropAndCalculateDose('${c.crop_id || c.crop}')" style="font-size:10.5px;padding:3px 8px;white-space:nowrap">
            Select & Dose ➜
          </button>
        </div>
      </div>
    `;
  });

  html += `
      </div>
    </div>
  `;

  resultsContainer.innerHTML = html;
  resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

window.selectCropAndCalculateDose = function(cropName) {
  const cropSelect = document.getElementById('target-crop-select');
  if (cropSelect) {
    for (let opt of cropSelect.options) {
      if (opt.value.toLowerCase() === cropName.toLowerCase()) {
        cropSelect.value = opt.value;
        break;
      }
    }
  }
  const mainCropSelect = document.getElementById('crop-name');
  if (mainCropSelect) {
    for (let opt of mainCropSelect.options) {
      if (opt.value.toLowerCase() === cropName.toLowerCase()) {
        mainCropSelect.value = opt.value;
        break;
      }
    }
  }
  triggerNutrientPlanForCrop(cropName);
};

window.triggerNutrientPlanForCrop = async function(cropOverride) {
  const crop = cropOverride || document.getElementById('target-crop-select')?.value || 'wheat';
  const acres = parseFloat(document.getElementById('target-crop-acres')?.value) || 2.5;

  const resultsContainer = document.getElementById('soil-action-results');
  if (resultsContainer) {
    resultsContainer.style.display = 'block';
    resultsContainer.innerHTML = `
      <div style="text-align:center;padding:16px;background:var(--ag-surface);border:1px solid var(--ag-border);border-radius:8px">
        <div style="font-size:24px;margin-bottom:6px">⚖️</div>
        <div style="font-weight:600;font-size:12px;color:var(--ag-text-primary)">Calibrating STCR Nutrient Equation for ${crop.toUpperCase()}...</div>
        <div style="font-size:11px;color:var(--ag-text-muted);margin-top:2px">Calculating exact commercial fertilizer bags (Urea, DAP, MOP)...</div>
      </div>
    `;
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  try {
    await confirmCurrentSoilValues();
    const lat = (window.currentCoords && window.currentCoords[0] && window.currentCoords[0][1]) || 30.90;
    const lng = (window.currentCoords && window.currentCoords[0] && window.currentCoords[0][0]) || 75.85;

    const plan = await apiNutrientPlan(currentSoilReportId, crop, acres, lat, lng);
    renderNutrientPlan(plan);
  } catch (err) {
    if (resultsContainer) {
      resultsContainer.innerHTML = `
        <div style="padding:12px;border-radius:8px;background:#fef2f2;border:1px solid #fecaca;color:#991b1b;font-size:12px">
          ⚠️ <strong>Calculation Error:</strong> ${err.message || 'Could not calculate fertilizer plan.'}
        </div>
      `;
    }
  }
};

function renderNutrientPlan(data) {
  const resultsContainer = document.getElementById('soil-action-results');
  if (!resultsContainer) return;

  const plan = data.fertilizer_plan || {};
  const perAcre = plan.commercial_fertilizers_per_acre || {};
  const totalField = plan.total_field_bags || {};
  const acres = data.field_size_acres || 1.0;
  const crop = data.crop || 'Crop';
  const hindi = data.hindi_guidance || {};

  let html = `
    <div class="nutrient-plan-card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;border-bottom:1px solid var(--ag-border);padding-bottom:8px">
        <div>
          <div style="font-weight:700;font-size:13px;color:var(--ag-text-primary)">🎯 Exact Fertilizer Prescription for ${crop.toUpperCase()}</div>
          <div style="font-size:11px;color:var(--ag-text-muted)">Calibrated for ${acres} Acres • STCR Soil-Test Crop-Response Equation</div>
        </div>
        <span style="font-size:11px;font-weight:700;padding:3px 8px;border-radius:6px;background:rgba(37,99,235,0.1);color:#2563eb">STCR Calibrated</span>
      </div>

      <!-- Fertilizer Bags Table / Row -->
      <div style="margin-bottom:12px">
        <div style="font-size:11px;font-weight:700;color:var(--ag-text-primary);margin-bottom:6px">Commercial Fertilizer Bags Needed:</div>
        
        <div class="fert-bag-row">
          <div style="display:flex;align-items:center;gap:8px">
            <span style="font-size:16px">⚪</span>
            <div>
              <div style="font-weight:700;font-size:12px;color:var(--ag-text-primary)">Neem-Coated Urea (45 kg bag)</div>
              <div style="font-size:10.5px;color:var(--ag-text-muted)">Nitrogen (N) supplier • Per acre: ${(perAcre.urea_45kg_bags || 0).toFixed(1)} bags</div>
            </div>
          </div>
          <div class="fert-bag-badge">${(totalField.urea_45kg_bags || 0).toFixed(1)} Bags</div>
        </div>

        <div class="fert-bag-row">
          <div style="display:flex;align-items:center;gap:8px">
            <span style="font-size:16px">🟤</span>
            <div>
              <div style="font-weight:700;font-size:12px;color:var(--ag-text-primary)">Di-Ammonium Phosphate (DAP 50 kg bag)</div>
              <div style="font-size:10.5px;color:var(--ag-text-muted)">Phosphorus (P) & Starter N • Per acre: ${(perAcre.dap_50kg_bags || 0).toFixed(1)} bags</div>
            </div>
          </div>
          <div class="fert-bag-badge">${(totalField.dap_50kg_bags || 0).toFixed(1)} Bags</div>
        </div>

        <div class="fert-bag-row">
          <div style="display:flex;align-items:center;gap:8px">
            <span style="font-size:16px">🔴</span>
            <div>
              <div style="font-weight:700;font-size:12px;color:var(--ag-text-primary)">Muriate of Potash (MOP 50 kg bag)</div>
              <div style="font-size:10.5px;color:var(--ag-text-muted)">Potassium (K) supplier • Per acre: ${(perAcre.mop_50kg_bags || 0).toFixed(1)} bags</div>
            </div>
          </div>
          <div class="fert-bag-badge">${(totalField.mop_50kg_bags || 0).toFixed(1)} Bags</div>
        </div>
      </div>

      <!-- Application Schedule & Split Timing -->
      <div style="background:rgba(241,245,249,0.5);border-radius:8px;padding:10px;margin-bottom:10px;font-size:11px">
        <div style="font-weight:700;color:var(--ag-text-primary);margin-bottom:4px">⏱️ Application Schedule:</div>
        <ul style="padding-left:16px;margin:0;color:var(--ag-text-muted);line-height:1.5">
          <li><strong>Basal Dose (बुवाई के समय):</strong> 100% DAP, 100% MOP, and 33-50% Urea applied at sowing time.</li>
          <li><strong>First Top Dressing (पहली टॉप ड्रेसिंग):</strong> Apply 25-33% Urea at first irrigation / 20-25 days after sowing.</li>
          <li><strong>Second Top Dressing (दूसरी टॉप ड्रेसिंग):</strong> Remaining Urea at flowering/tillering stage.</li>
        </ul>
      </div>

      <!-- Bilingual Hindi Guidance Card -->
      ${hindi.hindi_prescription ? `
        <div style="background:#fefce8;border:1px solid #fef08a;border-radius:8px;padding:10px;font-size:11px;color:#854d0e">
          <div style="font-weight:700;margin-bottom:4px">🇮🇳 किसान भाई के लिए खाद की सलाह:</div>
          <div style="line-height:1.4">${hindi.hindi_prescription}</div>
        </div>
      ` : ''}

      <div style="display:flex;justify-content:flex-end;margin-top:10px">
        <button type="button" class="btn btn-sm btn-outline" onclick="window.print()" style="font-size:11px;padding:4px 10px">
          🖨️ Print Prescription
        </button>
      </div>
    </div>
  `;

  resultsContainer.innerHTML = html;
  resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Attach dropzone listeners
function setupSoilDropzone() {
  const dropzone = document.getElementById('soil-dropzone');
  if (!dropzone) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('dragover');
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files.length > 0) {
      window.handleSoilFileUpload(files[0]);
    }
  }, false);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', setupSoilDropzone);
} else {
  setupSoilDropzone();
}

// ===== LIVE CROP REVENUE CALCULATOR (PANEL 4 IN FIELD ANALYTICS) =====

let yieldDebounceTimer = null;
window._currentIcarYield = 19.5;
window._currentRevenuePlotId = null;

window.loadRevenueCalculator = async function(customYield) {
  // Determine plot ID from active farmer or default
  let plotId = '00000000-0000-0000-0000-000000000001';
  if (typeof currentFarmer !== 'undefined' && currentFarmer && currentFarmer.plots && currentFarmer.plots.length > 0) {
    plotId = currentFarmer.plots[0].plot_id || plotId;
  }
  window._currentRevenuePlotId = plotId;

  try {
    const data = await apiGetRevenueEstimate(plotId, customYield);
    renderRevenueCalculator(data, customYield);
  } catch (err) {
    console.warn('Revenue calculator fetch note:', err);
    // Display graceful offline/fallback state
    const headline = document.getElementById('rev-headline-val');
    if (headline) headline.textContent = '₹ --,---';
    const note = document.getElementById('rev-better-text');
    if (note) note.textContent = 'Price data temporarily unavailable. Please retry shortly.';
  }
};

function renderRevenueCalculator(data, customYield) {
  if (!data) return;

  // 1. Headline Revenue Value
  const headlineEl = document.getElementById('rev-headline-val');
  if (headlineEl) {
    const est = data.estimated_revenue || 0;
    if (est >= 100000) {
      const lakhs = (est / 100000).toFixed(2);
      headlineEl.textContent = `₹ ${lakhs} Lakhs`;
      headlineEl.title = `Exact: ₹ ${Math.round(est).toLocaleString('en-IN')}`;
    } else {
      headlineEl.textContent = `₹ ${Math.round(est).toLocaleString('en-IN')}`;
    }
  }

  // 2. Crop & Plot Context
  const cropEl = document.getElementById('rev-crop-name');
  if (cropEl) cropEl.textContent = `${data.crop_display} (${data.crop_hi || data.crop})`;

  const areaEl = document.getElementById('rev-plot-area');
  if (areaEl) areaEl.textContent = data.area_acres;

  const locEl = document.getElementById('rev-location');
  if (locEl) locEl.textContent = `${data.district}, ${data.state}`;

  // 3. Harvest Volume Pill
  const harvestEl = document.getElementById('rev-total-harvest');
  if (harvestEl) harvestEl.textContent = `${data.total_yield_quintals} qtl`;

  // 4. Source Badge
  const badgeEl = document.getElementById('rev-source-badge');
  if (badgeEl) {
    badgeEl.textContent = data.price_source_label || 'Live · Agmarknet';
    if (data.market_price && data.market_price.source === 'agmarknet_live') {
      badgeEl.className = 'graph-badge badge-green';
    } else if (data.market_price && data.market_price.source === 'cached') {
      badgeEl.className = 'graph-badge badge-blue';
    } else {
      badgeEl.className = 'graph-badge badge-gold';
    }
  }

  // 5. Market Price Card
  const mktRateEl = document.getElementById('rev-market-rate');
  const mktLabelEl = document.getElementById('rev-market-label');
  const mktDateEl = document.getElementById('rev-market-date');
  if (data.market_price && data.market_price.modal_price_per_quintal) {
    if (mktRateEl) mktRateEl.innerHTML = `₹ ${Math.round(data.market_price.modal_price_per_quintal).toLocaleString('en-IN')} <span style="font-size:10px;font-weight:400">/ qtl</span>`;
    if (mktLabelEl) mktLabelEl.textContent = data.market_price.market || 'Local Mandi';
    if (mktDateEl) mktDateEl.textContent = `As of ${data.market_price.as_of_date}`;
  } else {
    if (mktRateEl) mktRateEl.textContent = 'Mkt N/A';
    if (mktLabelEl) mktLabelEl.textContent = 'No local trading reported';
    if (mktDateEl) mktDateEl.textContent = 'Showing MSP Floor';
  }

  // 6. MSP Floor Card
  const mspRateEl = document.getElementById('rev-msp-rate');
  const mspSeasonEl = document.getElementById('rev-msp-season');
  if (data.msp_rate && data.msp_rate.msp_per_quintal) {
    if (mspRateEl) mspRateEl.innerHTML = `₹ ${Math.round(data.msp_rate.msp_per_quintal).toLocaleString('en-IN')} <span style="font-size:10px;font-weight:400">/ qtl</span>`;
    if (mspSeasonEl) mspSeasonEl.textContent = `${data.msp_rate.season} ${data.msp_rate.year}`;
  } else {
    if (mspRateEl) mspRateEl.textContent = 'No MSP';
    if (mspSeasonEl) mspSeasonEl.textContent = 'Commercial Open Market';
  }

  // 7. Better Option Callout
  const betterTextEl = document.getElementById('rev-better-text');
  const calloutIconEl = document.getElementById('rev-callout-icon');
  if (betterTextEl) betterTextEl.innerHTML = data.better_option_summary;
  if (calloutIconEl) {
    if (data.better_channel === 'market') calloutIconEl.textContent = '📈';
    else if (data.better_channel === 'msp') calloutIconEl.textContent = '🏛️';
    else calloutIconEl.textContent = '💡';
  }

  // 8. Synchronize Yield Controls (only on initial load if customYield wasn't given)
  window._currentIcarYield = data.default_avg_yield_per_acre || 19.5;
  const numInput = document.getElementById('rev-yield-input');
  const slider = document.getElementById('rev-yield-slider');
  const icarLbl = document.getElementById('rev-icar-default-label');

  if (icarLbl) {
    icarLbl.textContent = `ICAR Baseline: ${window._currentIcarYield} q/acre`;
  }

  if (customYield == null) {
    if (numInput) numInput.value = data.expected_yield_per_acre;
    if (slider) {
      const base = window._currentIcarYield;
      slider.min = Math.max(1, Math.floor(base * 0.3));
      slider.max = Math.ceil(base * 2.2);
      slider.value = data.expected_yield_per_acre;
      const minLbl = document.getElementById('rev-slider-min-lbl');
      const maxLbl = document.getElementById('rev-slider-max-lbl');
      if (minLbl) minLbl.textContent = `Low (${slider.min} q)`;
      if (maxLbl) maxLbl.textContent = `High (${slider.max} q)`;
    }
  }
}

window.onYieldSliderInput = function(val) {
  const numInput = document.getElementById('rev-yield-input');
  if (numInput) numInput.value = val;
  debouncedRecalculateRevenue(parseFloat(val));
};

window.onYieldNumberInput = function(val) {
  const slider = document.getElementById('rev-yield-slider');
  if (slider) slider.value = val;
  debouncedRecalculateRevenue(parseFloat(val));
};

function debouncedRecalculateRevenue(yieldVal) {
  if (isNaN(yieldVal) || yieldVal <= 0) return;
  if (yieldDebounceTimer) clearTimeout(yieldDebounceTimer);
  yieldDebounceTimer = setTimeout(() => {
    window.loadRevenueCalculator(yieldVal);
  }, 300);
}

window.resetToIcarYield = function() {
  if (window._currentIcarYield) {
    const numInput = document.getElementById('rev-yield-input');
    const slider = document.getElementById('rev-yield-slider');
    if (numInput) numInput.value = window._currentIcarYield;
    if (slider) slider.value = window._currentIcarYield;
    window.loadRevenueCalculator(window._currentIcarYield);
  }
};


