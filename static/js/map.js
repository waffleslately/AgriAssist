// ===== REAL GOOGLE MAPS & SPATIAL LAYERS =====

// Centered on Punjab agricultural belt
const map = L.map('map', {
  center: [30.9025, 75.8525],
  zoom: 14,
  zoomControl: true
});

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
  document.getElementById('submit-btn').disabled = false;
  document.getElementById('clear-btn').style.display = 'inline-flex';
});

// Clear Event
document.getElementById('clear-btn').addEventListener('click', () => {
  drawnItems.clearLayers();
  window.currentCoords = null;
  updateBoundaryStatus(false);
  document.getElementById('submit-btn').disabled = true;
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
  document.getElementById('submit-btn').disabled = false;
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
