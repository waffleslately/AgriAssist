// ===== MAP SETUP =====
const map = L.map('map', {
  center: [22.5, 79.0],  // Center of India
  zoom: 5,
  zoomControl: true
});

// Satellite layer (Esri WorldImagery)
const satelliteLayer = L.tileLayer(
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  { attribution: 'Esri, Maxar, Earthstar Geographics', maxZoom: 19 }
).addTo(map);

// Labels overlay
const labelsLayer = L.tileLayer(
  'https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png',
  { attribution: 'CartoDB', opacity: 0.7, pane: 'overlayPane', maxZoom: 19 }
).addTo(map);

// Live cursor coordinates
map.on('mousemove', e => {
  document.getElementById('map-coords').textContent =
    `Lat: ${e.latlng.lat.toFixed(5)}  Lng: ${e.latlng.lng.toFixed(5)}`;
});

// ===== DRAW LAYER =====
const drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

const drawControl = new L.Control.Draw({
  edit: { featureGroup: drawnItems, remove: false },
  draw: {
    polygon: {
      allowIntersection: false,
      showArea: true,
      shapeOptions: { color: '#16a34a', fillColor: '#16a34a', fillOpacity: 0.18, weight: 2.5 }
    },
    polyline: false,
    rectangle: false,
    circle: false,
    marker: false,
    circlemarker: false
  }
});
map.addControl(drawControl);

// ===== STATE =====
window.drawnPolygon = null;
window.currentCoords = null;

// Listen to draw events
map.on(L.Draw.Event.CREATED, e => {
  drawnItems.clearLayers();
  drawnItems.addLayer(e.layer);
  const latlngs = e.layer.getLatLngs()[0];
  // Convert to [lng, lat] GeoJSON format
  window.currentCoords = latlngs.map(p => [p.lng, p.lat]);
  // Close the ring
  window.currentCoords.push(window.currentCoords[0]);

  // Fit map to drawn polygon
  map.fitBounds(e.layer.getBounds(), { padding: [40, 40] });

  updateBoundaryStatus(true);
  document.getElementById('submit-btn').disabled = false;
  document.getElementById('clear-btn').style.display = 'inline-flex';
});

// Clear handler
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
