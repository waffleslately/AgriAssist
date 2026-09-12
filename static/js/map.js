// ===== LEAFLET MAP & SPATIAL LAYERS =====
const map = L.map('map', {
  center: [30.9025, 75.8525], // Centered on Ludhiana, Punjab
  zoom: 13,
  zoomControl: true
});

// Satellite Layer (Esri WorldImagery)
const satelliteLayer = L.tileLayer(
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  { attribution: 'Esri, Maxar, Earthstar Geographics', maxZoom: 19 }
).addTo(map);

// OpenStreetMap Street View
const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: 'OpenStreetMap',
  maxZoom: 19
});

// Labels overlay
const labelsLayer = L.tileLayer(
  'https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png',
  { attribution: 'CartoDB', opacity: 0.75, pane: 'overlayPane', maxZoom: 19 }
).addTo(map);

// Layer control
L.control.layers({
  "🛰️ Satellite Imagery": satelliteLayer,
  "🗺️ OpenStreetMap": osmLayer
}, {
  "🏷️ Boundaries & Labels": labelsLayer
}, { position: 'topright' }).addTo(map);

// Live cursor coordinates
map.on('mousemove', e => {
  const el = document.getElementById('map-coords');
  if (el) {
    el.textContent = `Lat: ${e.latlng.lat.toFixed(5)}, Lng: ${e.latlng.lng.toFixed(5)}`;
  }
});

// ===== DRAW LAYER =====
const drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

// ===== DRONE PATCHES LAYER =====
const dronePatchesLayer = new L.FeatureGroup();
map.addLayer(dronePatchesLayer);

const drawControl = new L.Control.Draw({
  position: 'topleft',
  edit: { featureGroup: drawnItems, remove: false },
  draw: {
    polygon: {
      allowIntersection: false,
      showArea: true,
      shapeOptions: { color: '#16a34a', fillColor: '#16a34a', fillOpacity: 0.22, weight: 2.5 }
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

// Draw Event
map.on(L.Draw.Event.CREATED, e => {
  drawnItems.clearLayers();
  drawnItems.addLayer(e.layer);
  const latlngs = e.layer.getLatLngs()[0];
  window.currentCoords = latlngs.map(p => [p.lng, p.lat]);
  window.currentCoords.push(window.currentCoords[0]); // close ring

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

// Function to draw preset boundary on map
window.setBoundaryCoordinates = function(coords) {
  drawnItems.clearLayers();
  window.currentCoords = coords;

  const latlngs = coords.map(c => [c[1], c[0]]);
  const polygon = L.polygon(latlngs, {
    color: '#16a34a',
    fillColor: '#16a34a',
    fillOpacity: 0.22,
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

    // GeoJSON Polygon: [[[lng, lat], ...]]
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
