// ===== REAL GOOGLE MAPS & SPATIAL LAYERS =====

// Centered on Punjab agricultural belt
const map = L.map('map', {
  center: [30.9025, 75.8525],
  zoom: 14,
  zoomControl: true,
  preferCanvas: true
});
window.map = map;

// 1. Google Maps Real Satellite Hybrid (High-Resolution Satellite Imagery + Field Roads & Village Labels)
const googleHybrid = L.tileLayer('https://mt{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
  subdomains: ['0', '1', '2', '3'],
  attribution: '© Google Maps Real Satellite Data',
  maxZoom: 22
}).addTo(map);

// 2. Google Maps Pure Satellite Imagery
const googleSatellite = L.tileLayer('https://mt{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
  subdomains: ['0', '1', '2', '3'],
  attribution: '© Google Maps Satellite',
  maxZoom: 22
});

// 3. Google Maps Terrain (Contours & Elevation)
const googleTerrain = L.tileLayer('https://mt{s}.google.com/vt/lyrs=p&x={x}&y={y}&z={z}', {
  subdomains: ['0', '1', '2', '3'],
  attribution: '© Google Maps Terrain',
  maxZoom: 20
});

// 4. Google Maps Standard Roads
const googleRoads = L.tileLayer('https://mt{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
  subdomains: ['0', '1', '2', '3'],
  attribution: '© Google Maps Streets',
  maxZoom: 20
});

// 5. Esri WorldImagery Satellite
const esriSatellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
  attribution: 'Esri, Maxar, Earthstar',
  maxZoom: 19
});

// 6. OpenStreetMap
const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: 'OpenStreetMap',
  maxZoom: 19
});

// Real-time layer switcher control
L.control.layers({
  "🌍 Google Maps Hybrid (Satellite + Villages)": googleHybrid,
  "🛰️ Google Maps Pure Satellite": googleSatellite,
  "🏔️ Google Maps Terrain": googleTerrain,
  "🛣️ Google Maps Standard Roads": googleRoads,
  "🛰️ Esri WorldImagery Satellite": esriSatellite,
  "🗺️ OpenStreetMap": osm
}, null, { position: 'topright' }).addTo(map);

// Live cursor coordinates display
map.on('mousemove', e => {
  const el = document.getElementById('map-coords');
  if (el) {
    el.textContent = `Lat: ${e.latlng.lat.toFixed(5)}, Lng: ${e.latlng.lng.toFixed(5)} (Google Maps Real Data)`;
  }
});

// ===== DRAW LAYER FOR FARM PLOT =====
const drawnItems = new L.FeatureGroup();
window.drawnItems = drawnItems;
map.addLayer(drawnItems);

// ===== DRONE PATCHES LAYER =====
const dronePatchesLayer = new L.FeatureGroup();
map.addLayer(dronePatchesLayer);

// ===== SEARCH MARKER LAYER =====
const searchMarkerLayer = new L.FeatureGroup();
map.addLayer(searchMarkerLayer);

const drawControl = new L.Control.Draw({
  position: 'topleft',
  edit: { featureGroup: drawnItems, remove: false },
  draw: {
    polygon: {
      allowIntersection: false,
      showArea: true,
      shapeOptions: { color: '#22c55e', fillColor: '#22c55e', fillOpacity: 0.25, weight: 2.5 }
    },
    polyline: false,
    rectangle: false,
    circle: false,
    marker: false,
    circlemarker: false
  }
});
map.addControl(drawControl);

window.drawnPolygon = null;
window.currentCoords = null;

// Draw Creation Event
map.on(L.Draw.Event.CREATED, e => {
  drawnItems.clearLayers();
  drawnItems.addLayer(e.layer);
  const latlngs = e.layer.getLatLngs()[0];
  window.currentCoords = latlngs.map(p => [p.lng, p.lat]);
  window.currentCoords.push(window.currentCoords[0]); // auto-close

  map.fitBounds(e.layer.getBounds(), { padding: [40, 40] });

  updateBoundaryStatus(true);
  const submitBtn = document.getElementById('submit-btn');
  if (submitBtn) submitBtn.disabled = false;
  const stageBtn = document.getElementById('stage-btn');
  if (stageBtn) stageBtn.disabled = false;
  document.getElementById('clear-btn').style.display = 'inline-flex';
});

// Clear Event
document.getElementById('clear-btn').addEventListener('click', () => {
  drawnItems.clearLayers();
  window.currentCoords = null;
  updateBoundaryStatus(false);
  const submitBtn = document.getElementById('submit-btn');
  if (submitBtn) submitBtn.disabled = true;
  const stageBtn = document.getElementById('stage-btn');
  if (stageBtn) stageBtn.disabled = true;
  document.getElementById('clear-btn').style.display = 'none';
});

function updateBoundaryStatus(ready) {
  const dot = document.getElementById('status-dot');
  const label = document.getElementById('boundary-label');
  if (ready) {
    dot.classList.add('ready');
    const pts = (window.currentCoords.length - 1);
    label.textContent = `✅ Field boundary drawn (${pts} corners)`;
  } else {
    dot.classList.remove('ready');
    label.textContent = 'No boundary drawn yet';
  }
}

// Function to draw coordinates on map
window.setBoundaryCoordinates = function(coords) {
  drawnItems.clearLayers();
  window.currentCoords = coords;

  const latlngs = coords.map(c => [c[1], c[0]]);
  const polygon = L.polygon(latlngs, {
    color: '#22c55e',
    fillColor: '#22c55e',
    fillOpacity: 0.25,
    weight: 2.5
  });
  drawnItems.addLayer(polygon);
  map.fitBounds(polygon.getBounds(), { padding: [40, 40] });

  updateBoundaryStatus(true);
  const submitBtn = document.getElementById('submit-btn');
  if (submitBtn) submitBtn.disabled = false;
  const stageBtn = document.getElementById('stage-btn');
  if (stageBtn) stageBtn.disabled = false;
  document.getElementById('clear-btn').style.display = 'inline-flex';
};

// ===== RENDER DETECTED DRONE PATCHES ON MAP =====
window.renderDronePatchesOnMap = function(patches) {
  dronePatchesLayer.clearLayers();
  if (!patches || patches.length === 0) return;

  const patchColors = {
    healthy_stand:  { color: '#16a34a', fill: '#22c55e' },
    stressed_crop:  { color: '#ea580c', fill: '#f97316' },
    weed_cluster:   { color: '#9333ea', fill: '#a855f7' },
    bare_soil_gap:  { color: '#ca8a04', fill: '#eab308' }
  };

  const bounds = [];

  patches.forEach(p => {
    const geom = p.geojson_geometry;
    if (!geom || !geom.coordinates) return;

    const ring = geom.coordinates[0];
    const latlngs = ring.map(c => [c[1], c[0]]);
    const styling = patchColors[p.patch_type] || { color: '#3b82f6', fill: '#60a5fa' };

    const poly = L.polygon(latlngs, {
      color: styling.color,
      fillColor: styling.fill,
      fillOpacity: 0.55,
      weight: 2
    });

    const popupHtml = `
      <div style="min-width:180px">
        <div class="patch-popup-title" style="color:${styling.color}">
          ${p.patch_type.replace('_',' ').toUpperCase()}
        </div>
        <div class="patch-popup-item"><strong>Severity:</strong> ${p.severity_level}</div>
        <div class="patch-popup-item"><strong>Area:</strong> ${p.area_acres} acres (${p.percentage_of_plot}%)</div>
        ${p.mean_vigor_score ? `<div class="patch-popup-item"><strong>Mean Vigor:</strong> ${p.mean_vigor_score}</div>` : ''}
        <div class="patch-popup-item" style="margin-top:4px;color:#475569">${p.notes}</div>
      </div>
    `;
    poly.bindPopup(popupHtml);
    dronePatchesLayer.addLayer(poly);
    latlngs.forEach(pt => bounds.push(pt));
  });

  if (bounds.length > 0) {
    map.fitBounds(bounds, { padding: [40, 40] });
  }
};

// ===== GOOGLE MAPS REAL LOCATION SEARCH =====
window.searchMapLocation = async function() {
  const query = document.getElementById('map-search-input').value.trim();
  if (!query) return;

  const btn = document.querySelector('.btn-search');
  if (btn) btn.textContent = '...';

  try {
    const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query + ', India')}`);
    const data = await res.json();
    if (btn) btn.textContent = 'Search';

    if (data && data.length > 0) {
      const place = data[0];
      const lat = parseFloat(place.lat);
      const lon = parseFloat(place.lon);

      searchMarkerLayer.clearLayers();
      const marker = L.marker([lat, lon]).addTo(searchMarkerLayer);
      marker.bindPopup(`<b>📍 ${place.display_name}</b><br><small>Lat: ${lat.toFixed(5)}, Lon: ${lon.toFixed(5)}</small>`).openPopup();

      map.setView([lat, lon], 14);

      // Create a default field boundary in this real farm location
      const delta = 0.0022;
      const fieldCoords = [
        [lon - delta, lat - delta],
        [lon + delta, lat - delta],
        [lon + delta, lat + delta],
        [lon - delta, lat + delta],
        [lon - delta, lat - delta]
      ];
      window.setBoundaryCoordinates(fieldCoords);

      // Sync form district if name contains district
      const parts = place.display_name.split(',');
      if (parts.length > 1) {
        const districtInput = document.getElementById('district');
        if (districtInput) districtInput.value = parts[0].trim();
      }
    } else {
      alert(`Location "${query}" not found. Try searching by district or village name (e.g. "Ludhiana", "Baramati", "Yavatmal").`);
    }
  } catch (e) {
    if (btn) btn.textContent = 'Search';
    alert('Location search failed: ' + e.message);
  }
};


// ===== IOT LIVESTOCK TRACKING & GRAZING HEATMAP =====
let livestockLayer = L.layerGroup();
let grazingHeatLayer = null;
let livestockPollInterval = null;
let isHeatmapActive = false;

// Initialize layers when map is ready
document.addEventListener('DOMContentLoaded', () => {
  if (typeof map !== 'undefined' && map) {
    livestockLayer.addTo(map);
  }
});

window.openMapWithLivestock = function() {
  window.openMapModal();
  window.loadLiveLivestock();
  startLivestockPolling();
};

window.startLivestockPolling = function() {
  if (livestockPollInterval) clearInterval(livestockPollInterval);
  livestockPollInterval = setInterval(() => {
    if (document.getElementById('map-modal-overlay').style.display !== 'none' ||
        document.getElementById('tab-livestock')?.classList.contains('active')) {
      window.loadLiveLivestock(false);
    }
  }, 4000);
};

window.loadLiveLivestock = async function(fitBounds = true) {
  try {
    const res = await fetch('/api/v1/livestock/live');
    if (!res.ok) return;
    const data = await res.json();
    if (!data || !data.animals) return;

    // Update Tab UI summary metrics
    const totalCountEl = document.getElementById('ls-total-count');
    if (totalCountEl) totalCountEl.textContent = `${data.total_animals} Collars`;

    // Render roster list in Left Tab
    const rosterEl = document.getElementById('livestock-list');
    if (rosterEl) {
      rosterEl.innerHTML = data.animals.map(a => {
        const icon = a.animal_type === 'sheep' ? '🐑' : (a.animal_type === 'buffalo' ? '🐃' : '🐄');
        const batColor = a.battery_level > 50 ? '#16a34a' : (a.battery_level > 20 ? '#d97706' : '#dc2626');
        return `
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:6px 10px;display:flex;justify-content:space-between;align-items:center;font-size:11px">
            <div style="display:flex;align-items:center;gap:6px">
              <span style="font-size:15px">${icon}</span>
              <div>
                <div style="font-weight:700;color:#0f172a">${a.tag_id}</div>
                <div style="font-size:10px;color:#64748b">${a.status}</div>
              </div>
            </div>
            <div style="text-align:right">
              <span style="font-weight:600;color:${batColor}">🔋 ${a.battery_level}%</span>
              <div style="font-size:9.5px;color:#94a3b8">${a.latitude.toFixed(4)}, ${a.longitude.toFixed(4)}</div>
            </div>
          </div>
        `;
      }).join('');
    }

    // Render markers on map
    if (typeof map === 'undefined' || !map) return;
    if (!map.hasLayer(livestockLayer)) livestockLayer.addTo(map);
    livestockLayer.clearLayers();

    const bounds = [];
    data.animals.forEach(a => {
      const emoji = a.animal_type === 'sheep' ? '🐑' : (a.animal_type === 'buffalo' ? '🐃' : '🐄');
      const customIcon = L.divIcon({
        className: 'livestock-marker-pin',
        html: `<div style="background:#ffffff;border:2px solid #16a34a;border-radius:50%;width:34px;height:34px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,0.3);font-size:18px;position:relative">
                 ${emoji}
                 <span style="position:absolute;bottom:-14px;background:#0f172a;color:#fff;font-size:9px;font-weight:700;padding:1px 4px;border-radius:3px;white-space:nowrap">${a.tag_id}</span>
               </div>`,
        iconSize: [34, 34],
        iconAnchor: [17, 17]
      });

      const m = L.marker([a.latitude, a.longitude], { icon: customIcon }).addTo(livestockLayer);
      m.bindPopup(`
        <div style="font-family:Inter,sans-serif;font-size:12px;min-width:140px">
          <div style="font-weight:800;font-size:13px;margin-bottom:2px">${emoji} ${a.tag_id} (${a.animal_type})</div>
          <div style="color:#16a34a;font-weight:600;margin-bottom:4px">● ${a.status}</div>
          <div style="color:#64748b">Collar Battery: <b>${a.battery_level}%</b></div>
          <div style="color:#64748b;font-size:10.5px">GPS: ${a.latitude.toFixed(5)}, ${a.longitude.toFixed(5)}</div>
        </div>
      `);
      bounds.push([a.latitude, a.longitude]);
    });

    if (fitBounds && bounds.length > 0 && map.getBounds && !map.getBounds().contains(bounds[0])) {
      map.fitBounds(bounds, { padding: [60, 60], maxZoom: 17 });
    }

    // Also refresh grazing density analytics
    window.loadGrazingDensityAnalytics();

  } catch (err) {
    console.warn('[Livestock] Error fetching telemetry:', err);
  }
};

window.loadGrazingDensityAnalytics = async function() {
  try {
    const res = await fetch('/api/v1/livestock/grazing-density');
    if (!res.ok) return;
    const data = await res.json();
    if (!data || !data.analytics) return;

    const pressureEl = document.getElementById('ls-pressure-score');
    if (pressureEl) {
      const score = data.analytics.grazing_pressure_score;
      pressureEl.textContent = `${score}% (${data.analytics.pasture_status.split(' ')[0]})`;
      pressureEl.style.color = score > 75 ? '#dc2626' : (score > 40 ? '#d97706' : '#16a34a');
    }

    const intakeEl = document.getElementById('ls-intake-val');
    if (intakeEl) {
      intakeEl.textContent = `Est: ${data.analytics.estimated_daily_intake_kg} kg DM/day`;
    }

    const restDaysEl = document.getElementById('ls-resting-days');
    if (restDaysEl) {
      restDaysEl.textContent = `Rest: ${data.analytics.recommended_resting_days} Days`;
    }

    const adviceEl = document.getElementById('ls-advice-text');
    if (adviceEl) {
      adviceEl.textContent = data.analytics.actionable_advice;
    }

    // If heatmap layer is active, refresh its points
    if (isHeatmapActive && typeof L.heatLayer !== 'undefined' && map) {
      if (grazingHeatLayer) map.removeLayer(grazingHeatLayer);
      grazingHeatLayer = L.heatLayer(data.heatmap_points, {
        radius: 35,
        blur: 20,
        maxZoom: 17,
        gradient: { 0.2: '#22c55e', 0.5: '#eab308', 0.8: '#f97316', 1.0: '#ef4444' }
      }).addTo(map);
    }
  } catch (e) {
    console.warn('[Grazing] Analytics update failed:', e);
  }
};

window.toggleGrazingHeatmap = async function() {
  const btn = document.getElementById('btn-toggle-heat');
  if (isHeatmapActive) {
    // Turn off
    isHeatmapActive = false;
    if (grazingHeatLayer && map) map.removeLayer(grazingHeatLayer);
    if (btn) {
      btn.textContent = '🔥 Show Grazing Heatmap';
      btn.classList.remove('btn-primary');
      btn.classList.add('btn-outline');
    }
  } else {
    // Turn on
    isHeatmapActive = true;
    if (btn) {
      btn.textContent = '✖ Hide Grazing Heatmap';
      btn.classList.remove('btn-outline');
      btn.classList.add('btn-primary');
    }
    // Make sure map modal is open so farmer sees the heatmap
    if (document.getElementById('map-modal-overlay').style.display === 'none') {
      window.openMapModal();
    }
    await window.loadGrazingDensityAnalytics();
  }
};

window.triggerSimulateStep = async function() {
  try {
    const res = await fetch('/api/v1/iot/simulate-step', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ center_lat: 30.9025, center_lng: 75.8525, herd_size: 5 })
    });
    if (res.ok) {
      await window.loadLiveLivestock(false);
    }
  } catch (e) {
    console.error('Simulation step error:', e);
  }
};
