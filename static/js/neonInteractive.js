// ===== NEON INTERACTIVE CONTROLLER (THEME, DRONE SIMULATOR, ANALYTICS) =====

const NeonState = {
  droneSensorMode: 'ndvi',
  isFlying: false,
  dronePos: { x: 40, y: 30 },
  gridData: [],
  analyticsData: {
    2021: { rev: "₹ 1.92 L", rain: "420 mm", stress: "38.0%", note: "Conventional flood irrigation, high yellow rust incidence in lower field." },
    2022: { rev: "₹ 2.41 L", rain: "580 mm", stress: "34.0%", note: "Heavy monsoon, moderate waterlogging in lower khet; nitrogen leaching observed." },
    2023: { rev: "₹ 3.12 L", rain: "385 mm", stress: "21.0%", note: "Soil Health Card overrides adopted, NPK balance calibrated for Ludhiana loam." },
    2024: { rev: "₹ 4.25 L", rain: "640 mm", stress: "12.0%", note: "DGCA drone ultra-low volume spray introduced, weed clusters eradicated." },
    2025: { rev: "₹ 4.90 L", rain: "510 mm", stress: "8.5%", note: "Precision multispectral scouting; record wheat yield (25.5 quintals/Acre)." },
    2026: { rev: "₹ 5.40 L (Proj)", rain: "495 mm (Est)", stress: "6.8%", note: "AI forecasted yield based on current 0.74 Sentinel NDVI and healthy vigor." }
  }
};

// =========================================================
// 1. THEME SWITCHER (ORGANIC LIGHT <-> CYBER NEON DARK)
// =========================================================
window.toggleTheme = function() {
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  const nextTheme = current === 'light' ? 'dark' : 'light';
  
  document.documentElement.setAttribute('data-theme', nextTheme);
  localStorage.setItem('agriassist-theme', nextTheme);
  
  const icon = document.getElementById('theme-icon');
  const text = document.getElementById('theme-text');
  
  if (nextTheme === 'dark') {
    if (icon) icon.textContent = '⚡';
    if (text) text.textContent = 'Neon Black';
    showToast("⚡ Cyber Neon-Black Mode Activated!");
  } else {
    if (icon) icon.textContent = '🌓';
    if (text) text.textContent = 'Theme: Light';
    showToast("🌾 Organic Light Theme Activated!");
  }

  if (window.map) {
    try { window.map.invalidateSize(); } catch(e) {}
  }
  initDroneCanvas();
};

// Apply saved theme on page load
document.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('agriassist-theme');
  if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
    const icon = document.getElementById('theme-icon');
    const text = document.getElementById('theme-text');
    if (savedTheme === 'dark') {
      if (icon) icon.textContent = '⚡';
      if (text) text.textContent = 'Neon Black';
    }
  }
  initDroneCanvas();
});

// =========================================================
// 2. DRONE SIMULATOR 🚁
// =========================================================
window.initDroneCanvas = function() {
  const canvas = document.getElementById('drone-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  if (NeonState.gridData.length === 0) {
    for (let r = 0; r < 6; r++) {
      for (let c = 0; c < 14; c++) {
        let type = "healthy";
        if (r === 2 && (c === 4 || c === 5)) type = "weed";
        else if (r === 4 && (c >= 8 && c <= 10)) type = "stressed";
        else if (r === 0 && c === 12) type = "bare";
        NeonState.gridData.push({ row: r, col: c, type: type, scanned: false });
      }
    }
  }

  renderDroneCanvas(ctx, canvas);

  canvas.onclick = function(e) {
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    const colW = canvas.width / 14;
    const rowH = canvas.height / 6;
    const col = Math.floor(clickX / colW);
    const row = Math.floor(clickY / rowH);

    const cell = NeonState.gridData.find(g => g.row === row && g.col === col);
    if (cell) {
      let info = "";
      if (cell.type === 'healthy') info = "🟢 <strong>Zone Row " + (row+1) + ", Col " + (col+1) + "</strong>: Vigorous Canopy (NDVI 0.78). Chlorophyll optimum. Standard irrigation recommended.";
      else if (cell.type === 'weed') info = "🔴 <strong>Zone Row " + (row+1) + ", Col " + (col+1) + "</strong>: Invasive Weed Cluster (Phalaris minor). Targeted spot herbicide uploaded to mission.";
      else if (cell.type === 'stressed') info = "🟡 <strong>Zone Row " + (row+1) + ", Col " + (col+1) + "</strong>: Nitrogen Deficiency / Moisture Deficit (NDVI 0.46). Supplementary foliar urea spray advised.";
      else info = "🟤 <strong>Zone Row " + (row+1) + ", Col " + (col+1) + "</strong>: Emergence Gap. Soil exposed, check seed drill calibration.";
      
      const inspectEl = document.getElementById('zone-inspect-txt');
      if (inspectEl) inspectEl.innerHTML = info;
      showToast("Inspected Field Zone (" + (row+1) + ", " + (col+1) + ")");
    }
  };
};

function renderDroneCanvas(ctx, canvas) {
  if (!ctx || !canvas) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const colW = canvas.width / 14;
  const rowH = canvas.height / 6;
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

  NeonState.gridData.forEach(cell => {
    const x = cell.col * colW;
    const y = cell.row * rowH;

    let color = isDark ? "#091a11" : "#1b4332";
    if (NeonState.droneSensorMode === 'ndvi') {
      if (cell.type === 'healthy') color = cell.scanned ? (isDark ? "#00ff88" : "#22c55e") : (isDark ? "#062113" : "#1e4834");
      else if (cell.type === 'weed') color = cell.scanned ? (isDark ? "#ff2a5f" : "#ef4444") : (isDark ? "#2a0610" : "#4a2424");
      else if (cell.type === 'stressed') color = cell.scanned ? (isDark ? "#ffd166" : "#f59e0b") : (isDark ? "#2b2204" : "#483e20");
      else color = cell.scanned ? "#8c5b36" : (isDark ? "#17120e" : "#38291f");
    } else if (NeonState.droneSensorMode === 'rgb') {
      color = cell.type === 'bare' ? "#a87146" : (cell.type === 'weed' ? "#3f6212" : "#15803d");
    } else {
      color = cell.type === 'stressed' ? "#ff2a5f" : "#00f0ff";
    }

    ctx.fillStyle = color;
    ctx.fillRect(x + 1, y + 1, colW - 2, rowH - 2);
  });

  // RENDER THE DRONE 🚁
  ctx.save();
  ctx.font = "26px sans-serif";
  ctx.fillText("🚁", NeonState.dronePos.x - 13, NeonState.dronePos.y + 8);

  // Neon Ion Thruster Ring
  ctx.strokeStyle = isDark ? "#00ff88" : "rgba(116, 198, 157, 0.6)";
  ctx.lineWidth = isDark ? 2.5 : 1.5;
  if (isDark) {
    ctx.shadowColor = "#00ff88";
    ctx.shadowBlur = 10;
  }
  ctx.beginPath();
  ctx.arc(NeonState.dronePos.x, NeonState.dronePos.y, 22, 0, Math.PI * 2);
  ctx.stroke();
  ctx.restore();
}

window.setDroneSensorMode = function(mode) {
  NeonState.droneSensorMode = mode;
  document.querySelectorAll('.drone-mode-btn').forEach(b => b.classList.remove('active'));
  const activeBtn = document.getElementById('btn-mode-' + mode);
  if (activeBtn) activeBtn.classList.add('active');

  // Also sync the select dropdown if present
  const sensorSelect = document.getElementById('drone-sensor');
  if (sensorSelect) {
    if (mode === 'ndvi') sensorSelect.value = 'multispectral_ndvi';
    else if (mode === 'rgb') sensorSelect.value = 'rgb_vari';
    else if (mode === 'thermal') sensorSelect.value = 'thermal_canopy';
  }

  const canvas = document.getElementById('drone-canvas');
  if (canvas) renderDroneCanvas(canvas.getContext('2d'), canvas);
  showToast("Sensor set to: " + mode.toUpperCase());
};

window.startDroneFlightSimulation = function() {
  if (NeonState.isFlying) return;
  NeonState.isFlying = true;

  const btn = document.getElementById('drone-launch-btn');
  if (btn) {
    btn.innerHTML = "<span>🚁</span> Drone Scanning...";
    btn.disabled = true;
  }

  const canvas = document.getElementById('drone-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const waypoints = [
    { x: 30, y: 25 }, { x: 420, y: 25 },
    { x: 420, y: 65 }, { x: 30, y: 65 },
    { x: 30, y: 110 }, { x: 420, y: 110 },
    { x: 420, y: 155 }, { x: 30, y: 155 }
  ];

  let currentWpt = 0;
  const interval = setInterval(() => {
    const target = waypoints[currentWpt];
    const dx = target.x - NeonState.dronePos.x;
    const dy = target.y - NeonState.dronePos.y;

    NeonState.dronePos.x += dx * 0.16;
    NeonState.dronePos.y += dy * 0.16;

    const colW = canvas.width / 14;
    const rowH = canvas.height / 6;
    const col = Math.floor(NeonState.dronePos.x / colW);
    const row = Math.floor(NeonState.dronePos.y / rowH);
    const cell = NeonState.gridData.find(g => g.row === row && g.col === col);
    if (cell) cell.scanned = true;

    renderDroneCanvas(ctx, canvas);

    const scannedCount = NeonState.gridData.filter(g => g.scanned).length;
    const battEl = document.getElementById('hud-battery');
    const wptEl = document.getElementById('hud-wpt');
    const areaEl = document.getElementById('hud-area');

    if (battEl) battEl.textContent = Math.max(78, 98 - Math.floor(scannedCount / 4)) + "%";
    if (wptEl) wptEl.textContent = (currentWpt + 1) + " / " + waypoints.length;
    if (areaEl) areaEl.textContent = ((scannedCount / NeonState.gridData.length) * 3.8).toFixed(1) + " Ac";

    if (Math.abs(dx) < 6 && Math.abs(dy) < 6) {
      currentWpt++;
      if (currentWpt >= waypoints.length) {
        clearInterval(interval);
        NeonState.isFlying = false;
        if (btn) {
          btn.innerHTML = "<span>🚁</span> Launch Drone Flight Mission";
          btn.disabled = false;
        }
        showToast("🎉 Drone survey completed! Computing NDVI Grid...");
        if (typeof window.triggerDroneAnalysis === 'function') {
          window.triggerDroneAnalysis();
        }
      }
    }
  }, 45);
};

window.resetDroneCanvas = function() {
  NeonState.gridData.forEach(g => g.scanned = false);
  NeonState.dronePos = { x: 40, y: 30 };
  const wptEl = document.getElementById('hud-wpt');
  const areaEl = document.getElementById('hud-area');
  const battEl = document.getElementById('hud-battery');
  if (wptEl) wptEl.textContent = "0 / 8";
  if (areaEl) areaEl.textContent = "0.0 Ac";
  if (battEl) battEl.textContent = "98%";
  initDroneCanvas();
  showToast("Drone scan reset.");
};

// =========================================================
// 3. PEST CARDS & SEVERITY
// =========================================================
window.selectPestCard = function(elem, pestId) {
  document.querySelectorAll('.pest-card-item').forEach(c => c.classList.remove('selected'));
  if (elem) elem.classList.add('selected');

  // Sync with pest dropdown
  const pestKeySelect = document.getElementById('pest-key');
  if (pestKeySelect) pestKeySelect.value = pestId;

  const cropSelect = document.getElementById('pest-crop');
  if (cropSelect) {
    if (pestId === 'yellow_rust') cropSelect.value = 'wheat';
    else if (pestId === 'pink_bollworm' || pestId === 'whitefly') cropSelect.value = 'cotton';
    else if (pestId === 'fall_armyworm') cropSelect.value = 'maize';
    else if (pestId === 'blast' || pestId === 'yellow_stem_borer') cropSelect.value = 'paddy';
  }

  showToast("Selected pest: " + pestId.replace('_', ' ').toUpperCase());
};

window.updateSeverityIndicator = function(val) {
  const label = document.getElementById('severity-val');
  if (label) label.textContent = val + '%';

  const alertBox = document.getElementById('etl-alert-box');
  if (alertBox) {
    if (val >= 25) {
      alertBox.style.display = 'block';
      alertBox.innerHTML = `🚨 <strong>ETL Breached (${val}%)</strong>: Economic Threshold Level exceeded. Immediate CIBRC-approved drone spray mandatory.`;
      alertBox.style.background = 'var(--chart-red-bg)';
      alertBox.style.color = 'var(--chart-red-primary)';
      alertBox.style.borderLeftColor = 'var(--chart-red-primary)';
    } else if (val >= 10) {
      alertBox.style.display = 'block';
      alertBox.innerHTML = `⚠️ <strong>Approaching Critical Threshold (${val}%)</strong>: Monitor trap catch counts daily and prep bio-pesticide.`;
      alertBox.style.background = 'var(--chart-green-bg)';
      alertBox.style.color = 'var(--ag-wheat)';
      alertBox.style.borderLeftColor = 'var(--ag-wheat)';
    } else {
      alertBox.style.display = 'block';
      alertBox.innerHTML = `✅ <strong>Below Economic Threshold (${val}%)</strong>: Safe level. Continue natural predator biological control.`;
      alertBox.style.background = 'var(--chart-green-bg)';
      alertBox.style.color = 'var(--chart-green-primary)';
      alertBox.style.borderLeftColor = 'var(--chart-green-primary)';
    }
  }
};

window.testDroneSprayAnimation = function() {
  showToast("💨 Testing Centrifugal Spray Atomizer: 180 Micron Droplet Cloud Active!");
};

// =========================================================
// 4. ANALYTICS SYNCHRONIZED YEAR INSPECTOR (BLUE, GREEN, RED)
// =========================================================
window.selectAnalyticsYear = function(year) {
  const data = NeonState.analyticsData[year];
  if (!data) return;

  const syncBox = document.getElementById('analytics-sync-box');
  if (syncBox) {
    syncBox.innerHTML = `
      <div>
        <strong style="color:var(--ag-wheat);font-size:12px">📅 Year ${year} Synchronized Audit</strong>:
        <span style="color:var(--chart-blue-primary);margin-left:8px">🟦 Revenue: <strong>${data.rev}</strong></span> | 
        <span style="color:var(--chart-green-primary);margin-left:8px">🟩 Rainfall: <strong>${data.rain}</strong></span> | 
        <span style="color:var(--chart-red-primary);margin-left:8px">🟥 Stress Index: <strong>${data.stress}</strong></span>
        <div style="font-size:11px;color:var(--ag-text-muted);margin-top:4px;line-height:1.4">${data.note}</div>
      </div>
    `;
  }

  showToast(`Loaded ${year} synchronized multi-variable metrics!`);
};

// =========================================================
// 5. TOAST NOTIFICATION COMPONENT
// =========================================================
window.showToast = function(msg) {
  let t = document.getElementById('ag-toast');
  if (!t) {
    t = document.createElement('div');
    t.id = 'ag-toast';
    t.className = 'ag-toast';
    t.innerHTML = `<span>🌾</span> <span id="toast-text"></span>`;
    document.body.appendChild(t);
  }
  const textEl = document.getElementById('toast-text');
  if (textEl) textEl.textContent = msg;
  t.classList.add('show');
  clearTimeout(window._toastTimeout);
  window._toastTimeout = setTimeout(() => t.classList.remove('show'), 3500);
};

// =========================================================
// 6. TAB SWITCHING WITH CANVAS INIT HOOKS
// =========================================================
(function initTabSwitcher() {
  function switchTab(tabName) {
    // Deactivate all buttons and contents
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    // Activate the selected button
    const btn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    if (btn) btn.classList.add('active');

    // Activate the selected content
    const content = document.getElementById(`tab-${tabName}`);
    if (content) content.classList.add('active');

    // Tab-specific hooks
    if (tabName === 'drone') {
      setTimeout(() => {
        if (typeof window.initDroneCanvas === 'function') {
          window.initDroneCanvas();
        }
      }, 50);
    }

    if (tabName === 'analytics') {
      setTimeout(() => {
        // Select the last year by default to populate sync banner
        if (typeof window.selectAnalyticsYear === 'function') {
          window.selectAnalyticsYear(2026);
        }
      }, 50);
    }

    if (tabName === 'livestock') {
      // Trigger livestock map resize if needed
      if (window.map) {
        setTimeout(() => {
          try { window.map.invalidateSize(); } catch(e) {}
        }, 150);
      }
    }
  }

  // Expose globally so other scripts can call it
  window.switchTab = switchTab;

  // Attach click listeners to all tab buttons
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const tabName = btn.getAttribute('data-tab');
        if (tabName) switchTab(tabName);
      });
    });

    // Init drone canvas for default view
    if (typeof window.initDroneCanvas === 'function') {
      window.initDroneCanvas();
    }
  });
})();
