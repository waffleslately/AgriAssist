# 🌾 AgriAssist — Intelligent Farming & Drone Platform

A modular geospatial web platform for **Soil Health, Crop Nutrition, Drone Imagery Analysis, and Pest Diagnosis** built specifically for Indian agriculture (following **ICAR**, **CIBRC**, and **DGCA** guidelines).

---

## 🌟 Key Features

1. **Interactive Google Satellite Map (On-Demand Modal)**:
   - Real-time high-resolution satellite imagery (Google Hybrid, Satellite, Terrain, Esri WorldImagery).
   - Draw exact farm boundaries with polygon tools or search any Indian village/tehsil/district.
   - Map opens in a dedicated modal overlay, keeping the dashboard clean and fast.

2. **Save Multiple Lands & Simultaneous Batch Saving**:
   - Save multiple separate fields per farmer account (e.g., *North Field*, *Canal Side*, *Khasra 42*).
   - **➕ Add to Batch**: Draw land 1, set crop, add to batch; draw land 2, add to batch; then click **💾 Save All Lands at Same Time** to process and save all fields together.
   - **"My Farms Dashboard"**: Instantly view all your saved lands with live NDVI vigor badges (Healthy / Moderate / Stressed) and one-click map restoration.

3. **Sentinel-2 NDVI & 60-Day Historical Trend**:
   - Computes vegetation health and canopy moisture proxy.
   - Renders a 60-day NDVI trend inline SVG chart showing crop growth progress.

4. **Live 7-Day Weather Outlook & Rainfall Safety Guard**:
   - Fetches live 7-day daily forecasts (temperatures, precipitation) via Open-Meteo.
   - Flags heavy rain alerts (>15 mm in 48h) to advise holding fertilizer application and prevent nutrient runoff.

5. **ICAR STCR Fertilizer Prescription (9 Crops)**:
   - Soil Test Crop Response (STCR) calculations for: **Wheat, Paddy/Rice, Cotton, Soybean, Maize, Sugarcane, Mustard, Gram/Chickpea, and Sunflower**.
   - Converts nutrient deficits into commercial bag recommendations:
     - **Urea**: 45 kg bag (46% N)
     - **DAP**: 50 kg bag (18% N, 46% P₂O₅)
     - **MOP**: 50 kg bag (60% K₂O)
   - Supports manual ground-truth overrides (tested soil N/P/K/pH/OC and local rain gauge readings).

6. **Targeted Pest & Drone Diagnosis**:
   - Choose a specific target land from your saved lands to run diagnosis exclusively on that field.
   - Evaluates Economic Threshold Level (ETL) breaches against CIBRC approved guidelines.
   - Generates DGCA Ultra-Low Volume (ULV) drone spray prescriptions (10 L/acre, 1.8m flight altitude, 3.5 m/s speed).

7. **Multilingual Advisory**:
   - Field advisory cards available in 4 languages: **हिंदी (Hindi)**, **English**, **ਪੰਜਾਬੀ (Punjabi)**, and **मराठी (Marathi)**.
   - Instant WhatsApp sharing & print-ready farmer slips.

---

## 🚀 Quick Start Guide (For Team Members)

### Prerequisites
- **Python 3.10+** (Python 3.11, 3.12, 3.13, 3.14 supported)
- **Git** installed

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/waffleslately/AgriAssist.git
cd AgriAssist
```

---

### Step 2: Set Up Virtual Environment

#### On Windows (PowerShell / Command Prompt):
```powershell
python -m venv venv
.\venv\Scripts\activate
```
*(If PowerShell shows an execution policy warning, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and re-run).*

#### On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

### Step 4: Configure Environment File
```bash
# On Windows (PowerShell):
Copy-Item .env.example .env

# On macOS / Linux:
cp .env.example .env
```
*(No database setup required for local development — the platform has a built-in resilient in-memory mode for offline and local testing).*

---

### Step 5: Start the Local Development Server
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

### Step 6: Open the Application in Your Browser
- **🌐 Web App (Frontend)**: [http://127.0.0.1:8000/app](http://127.0.0.1:8000/app)
- **📖 Interactive API Docs (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **🔍 Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🧪 Running Automated Tests
To run the automated test suite (11 unit tests covering agronomy calculations, GeoJSON polygons, and pest engines):
```bash
pytest tests/ -v
```

---

## 🐳 Optional: Run with Docker Compose
If you prefer running with PostgreSQL + PostGIS via Docker:
```bash
docker-compose up -d --build
```
This starts:
- **FastAPI Backend + Frontend**: `http://localhost:8000/app`
- **PostgreSQL 16 + PostGIS 3.4**: `localhost:5432`
- **Redis Cache**: `localhost:6379`

---

## 📁 Project Architecture

```
AgriAssist/
├── app/
│   ├── main.py                     # FastAPI entrypoint & static frontend mount (/app)
│   ├── core/                       # Settings, security & logging
│   ├── db/                         # PostgreSQL session & base models
│   ├── models/                     # SQLAlchemy PostGIS & relational tables
│   ├── schemas/                    # Pydantic v2 schemas (plots, crops, drones, pest)
│   ├── services/
│   │   ├── agronomy_engine.py      # ICAR STCR fertilizer calculation (9 crops)
│   │   ├── gee_service.py          # Sentinel-2 NDVI & 60-day timeseries
│   │   ├── weather_service.py      # Open-Meteo 7-day live weather & rain alerts
│   │   ├── soil_service.py         # Soil Health Card benchmarks & fallbacks
│   │   ├── localization_service.py # 4-language advisory generator (EN/HI/PA/MR)
│   │   ├── drone_service.py        # Drone orthomosaic patch classification
│   │   └── pest_control_engine.py  # CIBRC IPM & DGCA drone spray parameters
│   └── api/v1/endpoints/           # Auth, plots, drone, pest, soil endpoints
├── static/                         # Single Page Application (Vanilla JS / HTML5)
│   ├── index.html                  # Full responsive dashboard & map modal
│   ├── css/app.css                 # Modern CSS design tokens & layouts
│   └── js/
│       ├── app.js                  # App state, batch staging & advisory renderers
│       ├── map.js                  # Leaflet.js + Google Maps satellite tile CDN
│       └── api.js                  # REST API client
├── tests/                          # 11 unit & integration pytest tests
├── requirements.txt                # Python dependencies
├── docker-compose.yml              # Multi-container setup
└── README.md                       # Documentation & setup guide
```

---

## 🤝 Troubleshooting & Access for Team Members

- **"Repository not found" or "Permission denied" when cloning**:
  - If your repository is **Private**, your team members must be invited as collaborators:
    1. Go to repository **Settings** on GitHub (`https://github.com/waffleslately/AgriAssist/settings/access`).
    2. Click **Collaborators** -> **Add people**.
    3. Enter their GitHub username or email address and click **Add**.
    4. They must accept the email invitation to clone and push code.
- **Port 8000 already in use**:
  - Run with another port: `uvicorn app.main:app --port 8080 --reload`
- **Satellite Map Not Loading**:
  - Leaflet fetches satellite tiles directly from Google Maps CDN (`mt0-mt3.google.com`). Ensure you have an active internet connection.
