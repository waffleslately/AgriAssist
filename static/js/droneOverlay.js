// ===== DRONE IMAGE OVERLAY & DEVELOPMENT HISTORY (PART A & PART B) =====

let _droneZoomLevel = 1.0;
let _activeDroneData = null;
let _originalLatestData = null;

/**
 * Initializes and renders Part A (Image Overlay with Zoom) and Part B (Crop Development History)
 */
window.renderDroneOverlayAndHistory = async function(data) {
  _activeDroneData = data;
  if (!_originalLatestData || data.scan_id === _originalLatestData.scan_id) {
    _originalLatestData = data;
  }

  // 1. Render Part A: Image Overlay
  renderDroneImageOverlay(data);

  // 2. Render Part B: Crop Development Over Time Chart
  const plotId = data.plot_id || (window.currentFarmer && window.currentFarmer.plots && window.currentFarmer.plots[0] ? window.currentFarmer.plots[0].plot_id : null);
  if (plotId) {
    await renderDevelopmentHistorySection(plotId, data.scan_id);
  } else {
    renderHistoryEmptyState("Run another scan in a few days to start tracking crop development over time.");
  }
};

/**
 * PART A: Renders the colored patch overlay directly on the uploaded drone image with zoom
 */
function renderDroneImageOverlay(data) {
  const container = document.getElementById('drone-image-overlay-card');
  if (!container) return;

  const farmerName = (window.currentFarmer && window.currentFarmer.name) || "Harpreet Singh";
  const plotName = data.plot_name || "Field Plot A1";
  const crop = (data.crop_name || "Wheat").toUpperCase();
  const acres = data.total_area_acres || 3.5;
  const altitude = data.flight_altitude_meters || 35;
  const sensor = (data.sensor_type || "multispectral_ndvi").replace('_', ' ').toUpperCase();
  const scanDate = data.scan_date || new Date().toISOString().split('T')[0];
  const imageUrl = data.image_url || "/static/img/drone_orthomosaic_preview.jpg";

  // Build cells and weed lists
  const cells = data.cells || (data.grid && data.grid.cells) || [];
  const weeds = data.weed_detections || (data.grid && data.grid.weed_cluster) || [];

  const isHistorical = _originalLatestData && data.scan_id !== _originalLatestData.scan_id;

  container.innerHTML = `
    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.05)">
      <!-- Plot Level Context Header -->
      <div style="display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid #f1f5f9;padding-bottom:10px;margin-bottom:10px">
        <div>
          <div style="font-size:15px;font-weight:800;color:#0f172a;display:flex;align-items:center;gap:6px">
            <span>🚁</span> ${plotName} — Drone Canopy Inspection
            ${isHistorical ? `<span style="background:#fef3c7;color:#92400e;font-size:10.5px;font-weight:700;padding:2px 8px;border-radius:12px;border:1px solid #fde68a">HISTORICAL SCAN: ${scanDate}</span>` : `<span style="background:#dcfce7;color:#166534;font-size:10.5px;font-weight:700;padding:2px 8px;border-radius:12px">LATEST SCAN</span>`}
          </div>
          <div style="font-size:11.5px;color:#64748b;margin-top:3px">
            Farmer: <strong>${farmerName}</strong> · Crop: <strong>${crop}</strong> · Area: <strong>${acres} Acres</strong> · Altitude: <strong>${altitude}m</strong> · Sensor: <strong>${sensor}</strong>
          </div>
        </div>
        ${isHistorical ? `
          <button type="button" class="btn btn-outline" style="font-size:11px;padding:4px 10px" onclick="returnToLatestScan()">
            ↺ Return to Latest Scan
          </button>
        ` : ''}
      </div>

      <!-- Zoom & Opacity Toolbar -->
      <div style="display:flex;justify-content:space-between;align-items:center;background:#f8fafc;padding:6px 12px;border-radius:6px;margin-bottom:10px;font-size:11.5px">
        <div style="display:flex;align-items:center;gap:8px">
          <span style="font-weight:700;color:#334155">Zoom:</span>
          <button type="button" class="btn" style="padding:2px 8px;background:#e2e8f0;font-size:12px" onclick="adjustDroneZoom(0.25)">🔍 +</button>
          <button type="button" class="btn" style="padding:2px 8px;background:#e2e8f0;font-size:12px" onclick="adjustDroneZoom(-0.25)">🔍 -</button>
          <button type="button" class="btn" style="padding:2px 8px;background:#e2e8f0;font-size:11px" onclick="resetDroneZoom()">↺ Reset</button>
          <span id="drone-zoom-val" style="font-weight:600;color:#64748b;min-width:40px">100%</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px">
          <span style="font-weight:700;color:#334155">Layer Opacity:</span>
          <input type="range" id="drone-opacity-slider" min="10" max="100" value="65" style="width:90px" oninput="adjustDroneOpacity(this.value)"/>
          <span id="drone-opacity-val" style="font-weight:600;color:#64748b;min-width:32px">65%</span>
        </div>
      </div>

      <!-- Interactive Image Viewport -->
      <div id="drone-viewport-container" style="position:relative;width:100%;height:380px;background:#0f172a;border-radius:8px;overflow:auto;display:flex;justify-content:center;align-items:center;border:1px solid #cbd5e1">
        <div id="drone-transform-stage" style="position:relative;display:inline-block;transform-origin:center center;transition:transform 0.15s ease">
          <!-- Raw Drone Photo -->
          <img id="drone-raw-photo" src="${imageUrl}" alt="Drone Orthomosaic" style="display:block;max-width:100%;max-height:360px;border-radius:4px;user-select:none" onerror="this.src='/static/img/drone_orthomosaic_preview.jpg'"/>
          
          <!-- Colored Patch Overlay (Absolute on top of image) -->
          <div id="drone-patch-layer" style="position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:auto;opacity:0.65">
            ${renderOverlayCells(cells)}
            ${renderOverlayWeeds(weeds)}
          </div>
        </div>
      </div>

      <!-- Patch Inspector Detail Card -->
      <div id="drone-patch-inspector" style="margin-top:10px;padding:8px 12px;background:#f8fafc;border:1px dashed #cbd5e1;border-radius:6px;font-size:11.5px;display:flex;justify-content:space-between;align-items:center">
        <div>
          <span style="font-weight:700;color:#334155">🔍 Patch Inspector:</span>
          <span id="inspector-msg" style="color:#64748b;margin-left:6px">Click any colored cell or purple weed marker on the photo to inspect NDVI & treatment.</span>
        </div>
        <div id="inspector-badge"></div>
      </div>

      <!-- Color Legend -->
      <div style="display:flex;flex-wrap:wrap;gap:12px;margin-top:10px;padding-top:8px;border-top:1px solid #f1f5f9;font-size:11px">
        <div style="display:flex;align-items:center;gap:4px"><span style="display:inline-block;width:12px;height:12px;background:#22c55e;border-radius:2px"></span> <strong>Healthy</strong> (NDVI > 0.60)</div>
        <div style="display:flex;align-items:center;gap:4px"><span style="display:inline-block;width:12px;height:12px;background:#eab308;border-radius:2px"></span> <strong>Moderate</strong> (0.30 - 0.60)</div>
        <div style="display:flex;align-items:center;gap:4px"><span style="display:inline-block;width:12px;height:12px;background:#ef4444;border-radius:2px"></span> <strong>Stressed/Bare</strong> (< 0.30)</div>
        <div style="display:flex;align-items:center;gap:4px"><span style="display:inline-block;width:12px;height:12px;background:#9333ea;border-radius:50%"></span> <strong>Weed Cluster 🌿</strong></div>
      </div>
    </div>
  `;
  _droneZoomLevel = 1.0;
}

function renderOverlayCells(cells) {
  if (!cells || cells.length === 0) return '';
  return cells.map((c, i) => {
    const left = (c.norm_x !== undefined ? c.norm_x * 100 : (c.x || 0)) + '%';
    const top = (c.norm_y !== undefined ? c.norm_y * 100 : (c.y || 0)) + '%';
    const width = (c.norm_w !== undefined ? c.norm_w * 100 : 3.0) + '%';
    const height = (c.norm_h !== undefined ? c.norm_h * 100 : 3.0) + '%';

    let bg = '#22c55e';
    let label = 'Healthy Stand';
    if (c.status === 'moderate') {
      bg = '#eab308';
      label = 'Moderate Vigor';
    } else if (c.status === 'stressed_or_bare') {
      bg = '#ef4444';
      label = 'Stressed / Bare Soil';
    }

    const cellData = JSON.stringify({
      type: 'canopy',
      status: label,
      color: bg,
      ndvi: c.ndvi,
      lat: c.lat,
      lon: c.lon,
      action: c.action || `NDVI ${c.ndvi} — monitor crop canopy.`
    }).replace(/"/g, '&quot;');

    return `
      <div class="drone-overlay-box" 
           style="position:absolute;left:${left};top:${top};width:${width};height:${height};background:${bg};border:0.5px solid rgba(255,255,255,0.4);cursor:pointer"
           onclick="inspectDronePatch(this, '${cellData}')"
           title="${label} (NDVI: ${c.ndvi})">
      </div>
    `;
  }).join('');
}

function renderOverlayWeeds(weeds) {
  if (!weeds || weeds.length === 0) return '';
  return weeds.map(w => {
    const left = (w.norm_x !== undefined ? w.norm_x * 100 : 50) + '%';
    const top = (w.norm_y !== undefined ? w.norm_y * 100 : 50) + '%';
    const conf = Math.round((w.confidence || 0.88) * 100);

    const weedData = JSON.stringify({
      type: 'weed',
      status: 'Weed Cluster 🌿',
      color: '#9333ea',
      confidence: conf,
      lat: w.lat,
      lon: w.lon,
      action: w.action || `Weed cluster detected (${conf}% confidence). Apply targeted spot herbicide.`
    }).replace(/"/g, '&quot;');

    return `
      <div style="position:absolute;left:${left};top:${top};transform:translate(-50%,-50%);width:18px;height:18px;background:#9333ea;color:#fff;border:2px solid #fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;box-shadow:0 2px 4px rgba(0,0,0,0.5);cursor:pointer;z-index:10"
           onclick="inspectDronePatch(this, '${weedData}')"
           title="Weed Cluster (${conf}%)">
        🌿
      </div>
    `;
  }).join('');
}

window.inspectDronePatch = function(el, rawJson) {
  try {
    const data = JSON.parse(rawJson);
    const msgEl = document.getElementById('inspector-msg');
    const badgeEl = document.getElementById('inspector-badge');
    if (!msgEl) return;

    if (data.type === 'weed') {
      msgEl.innerHTML = `<strong style="color:#9333ea">${data.status}</strong> (Confidence: <strong>${data.confidence}%</strong>) · GPS: ${data.lat ? data.lat.toFixed(5) + ', ' + data.lon.toFixed(5) : 'N/A'}<br><span style="color:#475569">💡 <strong>Suggested Action:</strong> ${data.action}</span>`;
      badgeEl.innerHTML = `<span style="background:#faf5ff;border:1px solid #d8b4fe;color:#7e22ce;padding:3px 8px;border-radius:12px;font-weight:700">Weed Hotspot</span>`;
    } else {
      msgEl.innerHTML = `<strong style="color:${data.color}">${data.status}</strong> · NDVI Score: <strong>${data.ndvi}</strong> · GPS: ${data.lat ? data.lat.toFixed(5) + ', ' + data.lon.toFixed(5) : 'N/A'}<br><span style="color:#475569">💡 <strong>Suggested Action:</strong> ${data.action}</span>`;
      badgeEl.innerHTML = `<span style="background:${data.color}22;border:1px solid ${data.color};color:${data.color};padding:3px 8px;border-radius:12px;font-weight:700">NDVI: ${data.ndvi}</span>`;
    }
  } catch (e) {
    console.error("Inspect patch error:", e);
  }
};

window.adjustDroneZoom = function(delta) {
  _droneZoomLevel = Math.max(0.5, Math.min(3.0, _droneZoomLevel + delta));
  const stage = document.getElementById('drone-transform-stage');
  const label = document.getElementById('drone-zoom-val');
  if (stage) stage.style.transform = `scale(${_droneZoomLevel})`;
  if (label) label.textContent = `${Math.round(_droneZoomLevel * 100)}%`;
};

window.resetDroneZoom = function() {
  _droneZoomLevel = 1.0;
  const stage = document.getElementById('drone-transform-stage');
  const label = document.getElementById('drone-zoom-val');
  if (stage) stage.style.transform = 'scale(1)';
  if (label) label.textContent = '100%';
};

window.adjustDroneOpacity = function(val) {
  const layer = document.getElementById('drone-patch-layer');
  const label = document.getElementById('drone-opacity-val');
  if (layer) layer.style.opacity = val / 100.0;
  if (label) label.textContent = `${val}%`;
};

window.returnToLatestScan = function() {
  if (_originalLatestData) {
    window.renderDroneOverlayAndHistory(_originalLatestData);
  }
};

// ============================================================
// PART B: CROP DEVELOPMENT OVER TIME (TREND CHART & SWAPPER)
// ============================================================

async function renderDevelopmentHistorySection(plotId, currentScanId) {
  const container = document.getElementById('drone-history-card');
  if (!container) return;

  try {
    const historyData = await apiGetDevelopmentHistory(plotId);
    const scans = (historyData && historyData.scans) || [];

    if (scans.length < 2) {
      renderHistoryEmptyState("Run another scan in a few days to start tracking crop development over time.", plotId);
      return;
    }

    renderTrendChart(container, historyData, currentScanId);
  } catch (e) {
    console.warn("Could not fetch development history:", e);
    renderHistoryEmptyState("Run another scan in a few days to start tracking crop development over time.", plotId);
  }
}

function renderHistoryEmptyState(msg, plotId) {
  const container = document.getElementById('drone-history-card');
  if (!container) return;

  container.innerHTML = `
    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin-bottom:16px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
        <span style="font-size:18px">📈</span>
        <div style="font-size:14px;font-weight:800;color:#0f172a">Crop Development Over Time</div>
      </div>
      <div style="background:#f8fafc;border:1px dashed #cbd5e1;border-radius:8px;padding:18px;text-align:center">
        <div style="font-size:24px;margin-bottom:6px">🌱</div>
        <div style="font-weight:700;color:#334155;margin-bottom:4px">${msg}</div>
        <div style="font-size:11.5px;color:#64748b;max-width:380px;margin:0 auto 12px">
          With multiple scans across the season, you'll see NDVI vigor progress curves and stacked health area distributions.
        </div>
        ${plotId ? `
          <button type="button" class="btn btn-outline" style="font-size:11px;padding:5px 12px" onclick="createDemoPreviousScan('${plotId}')">
            🧪 Populate Demo Previous Scan (2 Weeks Ago)
          </button>
        ` : ''}
      </div>
    </div>
  `;
}

function renderTrendChart(container, historyData, currentScanId) {
  const scans = historyData.scans;
  const crop = (historyData.crop || "Wheat").toUpperCase();
  const plotName = historyData.plot_name || "Field";

  // Compute chart points for NDVI line chart
  const dates = scans.map(s => s.scan_date);
  const ndvis = scans.map(s => s.avg_ndvi !== null ? s.avg_ndvi : 0.5);

  const minNdvi = Math.max(0.0, Math.min(...ndvis) - 0.1);
  const maxNdvi = Math.min(1.0, Math.max(...ndvis) + 0.1);
  const ndviRange = Math.max(0.1, maxNdvi - minNdvi);

  const svgWidth = 460;
  const svgHeight = 130;
  const padding = 30;

  const points = scans.map((s, idx) => {
    const x = padding + (idx / Math.max(1, scans.length - 1)) * (svgWidth - 2 * padding);
    const y = svgHeight - padding - (((s.avg_ndvi || 0.5) - minNdvi) / ndviRange) * (svgHeight - 2 * padding);
    return { x, y, scan: s };
  });

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');

  container.innerHTML = `
    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.05)">
      <!-- Header -->
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
        <div>
          <div style="font-size:15px;font-weight:800;color:#0f172a;display:flex;align-items:center;gap:6px">
            <span>📈</span> Crop Development Over Time
            <span style="font-size:11px;font-weight:600;background:#f1f5f9;color:#475569;padding:2px 8px;border-radius:12px">${scans.length} Historical Scans</span>
          </div>
          <div style="font-size:11.5px;color:#64748b;margin-top:2px">
            Vegetation growth trend for <strong>${plotName} (${crop})</strong> · Click any date point to swap drone photo
          </div>
        </div>
      </div>

      <!-- 1. NDVI Trend Line Chart (SVG) -->
      <div style="margin-bottom:14px">
        <div style="display:flex;justify-content:space-between;font-size:11px;color:#64748b;margin-bottom:4px">
          <span><strong>Average NDVI Vigor Trend</strong> (Chlorophyll Biomass)</span>
          <span>Higher is healthier (0.0 to 1.0)</span>
        </div>
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px 6px;position:relative">
          <svg viewBox="0 0 ${svgWidth} ${svgHeight}" style="width:100%;height:130px;overflow:visible">
            <!-- Grid lines -->
            <line x1="${padding}" y1="${padding}" x2="${svgWidth - padding}" y2="${padding}" stroke="#e2e8f0" stroke-dasharray="3,3"/>
            <line x1="${padding}" y1="${svgHeight/2}" x2="${svgWidth - padding}" y2="${svgHeight/2}" stroke="#e2e8f0" stroke-dasharray="3,3"/>
            <line x1="${padding}" y1="${svgHeight - padding}" x2="${svgWidth - padding}" y2="${svgHeight - padding}" stroke="#cbd5e1"/>

            <!-- Area fill -->
            <path d="${pathD} L ${points[points.length-1].x} ${svgHeight - padding} L ${points[0].x} ${svgHeight - padding} Z" fill="rgba(34, 197, 94, 0.12)"/>

            <!-- Trend Line -->
            <path d="${pathD}" fill="none" stroke="#16a34a" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>

            <!-- Interactive Clickable Points -->
            ${points.map(p => {
              const isSelected = p.scan.scan_id === currentScanId;
              return `
                <g style="cursor:pointer" onclick="swapScanOverlay('${p.scan.scan_id}')">
                  <circle cx="${p.x}" cy="${p.y}" r="${isSelected ? 7 : 5}" fill="${isSelected ? '#16a34a' : '#ffffff'}" stroke="#16a34a" stroke-width="${isSelected ? 3 : 2}"/>
                  <text x="${p.x}" y="${p.y - 10}" text-anchor="middle" font-size="10.5" font-weight="700" fill="#0f172a">${p.scan.avg_ndvi ? p.scan.avg_ndvi.toFixed(2) : '—'}</text>
                  <text x="${p.x}" y="${svgHeight - 12}" text-anchor="middle" font-size="9.5" fill="#64748b">${p.scan.scan_date}</text>
                </g>
              `;
            }).join('')}
          </svg>
        </div>
      </div>

      <!-- 2. Stacked 3-Color Health Area Bar per Scan -->
      <div>
        <div style="display:flex;justify-content:space-between;font-size:11px;color:#64748b;margin-bottom:6px">
          <span><strong>Canopy Area Health Distribution</strong> (Click to view scan)</span>
          <div style="display:flex;gap:8px">
            <span style="color:#16a34a">● Healthy %</span>
            <span style="color:#ca8a04">● Moderate %</span>
            <span style="color:#dc2626">● Stressed %</span>
          </div>
        </div>

        <div style="display:flex;flex-direction:column;gap:8px">
          ${scans.map(s => {
            const isSelected = s.scan_id === currentScanId;
            return `
              <div style="display:flex;align-items:center;gap:10px;padding:6px 10px;border-radius:6px;background:${isSelected ? '#f0fdf4' : '#f8fafc'};border:1px solid ${isSelected ? '#86efac' : '#e2e8f0'};cursor:pointer;transition:all 0.15s ease"
                   onclick="swapScanOverlay('${s.scan_id}')"
                   title="Click to view drone photo and patches for ${s.scan_date}">
                <div style="width:85px;font-size:11.5px;font-weight:${isSelected ? '800' : '600'};color:${isSelected ? '#166534' : '#334155'}">
                  ${s.scan_date}
                </div>
                
                <!-- Stacked 3-color bar -->
                <div style="flex:1;height:16px;background:#e2e8f0;border-radius:4px;overflow:hidden;display:flex">
                  <div style="width:${s.healthy_pct}%;background:#22c55e" title="Healthy: ${s.healthy_pct}%"></div>
                  <div style="width:${s.moderate_pct}%;background:#eab308" title="Moderate: ${s.moderate_pct}%"></div>
                  <div style="width:${s.stressed_pct}%;background:#ef4444" title="Stressed: ${s.stressed_pct}%"></div>
                </div>

                <div style="width:110px;font-size:10.5px;text-align:right;color:#475569">
                  <span style="color:#16a34a;font-weight:700">${Math.round(s.healthy_pct)}%</span> /
                  <span style="color:#ca8a04;font-weight:700">${Math.round(s.moderate_pct)}%</span> /
                  <span style="color:#dc2626;font-weight:700">${Math.round(s.stressed_pct)}%</span>
                </div>

                ${isSelected ? `<span style="font-size:11px;color:#16a34a;font-weight:700">● Active</span>` : `<span style="font-size:10px;color:#94a3b8">View ➔</span>`}
              </div>
            `;
          }).join('')}
        </div>
      </div>
    </div>
  `;
}

window.swapScanOverlay = async function(scanId) {
  try {
    showLoading('Loading Historical Scan Data...');
    const detail = await apiGetScanDetail(scanId);
    hideLoading();

    if (detail && detail.grid) {
      const formattedData = {
        scan_id: detail.scan_id,
        plot_id: detail.plot_id,
        scan_date: detail.scan_date.split('T')[0],
        crop_name: (_originalLatestData && _originalLatestData.crop_name) || "Wheat",
        total_area_acres: (_originalLatestData && _originalLatestData.total_area_acres) || 3.5,
        sensor_type: detail.grid.sensor_type || (_originalLatestData && _originalLatestData.sensor_type) || "multispectral_ndvi",
        image_url: detail.grid.image_url || "/static/img/drone_orthomosaic_preview.jpg",
        cells: detail.grid.cells || [],
        weed_detections: detail.grid.weed_detections || detail.grid.weed_cluster || [],
        grid: detail.grid
      };

      // Re-render Part A with historical scan
      renderDroneImageOverlay(formattedData);

      // Re-highlight Part B chart
      renderDevelopmentHistorySection(detail.plot_id, detail.scan_id);
    }
  } catch (e) {
    hideLoading();
    alert("Could not load past scan: " + e.message);
  }
};

window.createDemoPreviousScan = async function(plotId) {
  try {
    showLoading('Generating historical baseline scan (2 weeks ago)...');
    // Call analyze with synthetic baseline to populate past record
    const res = await fetch('/api/v1/drone/seed-demo-history/' + plotId, { method: 'POST' });
    hideLoading();
    if (res.ok) {
      renderDevelopmentHistorySection(plotId, _activeDroneData ? _activeDroneData.scan_id : null);
    } else {
      // Fallback: reload history
      renderDevelopmentHistorySection(plotId, null);
    }
  } catch (e) {
    hideLoading();
    // Re-render
    renderDevelopmentHistorySection(plotId, null);
  }
};
