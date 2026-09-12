HEAD
﻿# India Agri-Advisory Platform (Backend & Frontend)

Production-grade, modular geospatial platform for **Soil, Crop, Drone & Pest Advisory** scoped specifically for Indian agriculture (ICAR, CIBRC, and DGCA standards).

---

## 🌟 Key Features

1. **Interactive Web Frontend (`/app`)**:
   - Leaflet.js interactive satellite map with full polygon draw tool for farm boundaries.
   - Live plot onboarding form with bilingual language toggle (Hindi / English).
   - Real-time advisory visualization: acreage, Sentinel-2 NDVI health meter, 48h rainfall alert, soil nutrient status, and commercial fertilizer bags per acre (Urea, DAP, MOP).
   - Dedicated **Pest & Disease Diagnosis tab** with economic threshold evaluations and drone flight prescriptions.

2. **Spatial Plot Onboarding (`/api/v1/plots/onboard`)**:
   - Accepts GeoJSON polygon boundary drawn by farmer.
   - Calculates geodesic acreage in acres.
   - Validates coordinates, boundary closure, and orientation.

3. **PostGIS Spatial Soil Health Card Query**:
   - Queries nearest lab-tested Soil Health Card reference points using PostGIS `<->` spatial operator.
   - Graceful fallback to state/district ICAR agro-climatic fertility benchmarks if no sample exists within 15 km.

4. **Google Earth Engine (GEE) Dual-Mode Adapter**:
   - **Live Mode**: Queries Sentinel-2 Surface Reflectance (`COPERNICUS/S2_SR_HARMONIZED`), performs cloud-masking (<30%), computes mean NDVI and NDMI moisture over plot geometry.
   - **Dev Simulation Mode**: Out-of-the-box local development and testing without requiring immediate GEE service account credentials.

5. **Weather Safety Guard (Open-Meteo)**:
   - Evaluates 7-day rainfall forecast; flags **heavy rain alerts (>15 mm in 48h)** to hold nitrogen broadcasting and prevent fertilizer runoff.

6. **Agronomy Rule Engine (ICAR Aligned)**:
   - Soil Test Crop Response (STCR) adjustment factors: Low (+25%), Medium (100%), High (-25%).
   - Translates N-P-K nutrient deficits into standard **Indian commercial bags**:
     - **Urea**: 45 kg bag (46% N)
     - **DAP**: 50 kg bag (18% N, 46% P₂O₅)
     - **MOP**: 50 kg bag (60% K₂O)
   - Crop stages supported: Paddy, Wheat, Cotton, Soybean, Maize.

7. **Drone Orthomosaic Patch Detection (`/api/v1/drone/surveys`)**:
   - Ingests drone aerial imagery or spatial orthomosaics.
   - Identifies sub-plot vigor zones: `healthy_stand`, `stressed_crop`, `bare_soil_gap`, and `weed_cluster`.
   - Computes affected area in acres and spatial polygon boundaries.

8. **Pest & Disease Diagnosis with DGCA Drone Prescriptions (`/api/v1/pest/diagnose`)**:
   - Evaluates Economic Threshold Level (ETL) breaches against CIBRC approved guidelines.
   - Generates three-tier Integrated Pest Management (IPM): Cultural, Biological, and Chemical.
   - Computes **DGCA Ultra-Low Volume (ULV) Drone Spray Missions** (10 L/acre, 1.8m flight altitude, 3.5 m/s speed, anti-drift nozzles).

9. **Bilingual Advisory Cards**:
   - Auto-generates farmer-friendly advice in **Hindi** (हिंदी) and **English** with exact bag quantities per acre.

---

## 📁 Directory Structure

```
agri-backend/
├── docker-compose.yml              # PostgreSQL 16 + PostGIS 3.4, Redis, FastAPI App
├── Dockerfile                      # Python 3.11 with GDAL, GEOS, PROJ system libs
├── requirements.txt                # FastAPI, GeoAlchemy2, Shapely, GEE, SQLAlchemy
├── .env.example                    # Environment settings template
├── .gitignore                      # Git ignore rules for Python, virtualenv & secrets
├── alembic.ini                     # Migration configuration
├── alembic/
│   ├── env.py                      # Async PostGIS-aware migration engine
│   └── versions/
│       └── 0001_initial_postgis_schema.py  # DDL with spatial GiST indexes
├── static/                         # Web Frontend Single Page Application
│   ├── index.html                  # Leaflet map, tabs, bilingual forms & cards
│   ├── css/
│   │   └── app.css                 # Clean responsive design & metrics styles
│   └── js/
│       ├── map.js                  # Leaflet map, Esri WorldImagery & polygon draw
│       ├── api.js                  # REST API client
│       └── app.js                  # Dynamic UI rendering & tab controller
├── app/
│   ├── main.py                     # FastAPI entrypoint, CORS, static file mount
│   ├── core/                       # App settings, security & JWT
│   ├── db/                         # Async sessionmaker & base
│   ├── models/                     # PostGIS & relational SQLAlchemy models
│   ├── schemas/                    # Pydantic v2 schemas & GeoJSON validators
│   ├── services/
│   │   ├── gee_service.py          # Dual-mode Sentinel-2 client
│   │   ├── weather_service.py      # 7-day precipitation & forecast
│   │   ├── soil_service.py         # Spatial SHC lookup + fallback
│   │   ├── agronomy_engine.py      # Fertilizer dose & bag converter
│   │   ├── drone_service.py        # Orthomosaic sub-plot patch classifier
│   │   ├── pest_control_engine.py  # CIBRC IPM & DGCA drone prescription
│   │   └── localization_service.py # Hindi/English advisory cards
│   ├── seeds/                      # ICAR crop guidelines & soil baselines
│   └── api/v1/
│       ├── api.py                  # Router aggregator (9 routers)
│       └── endpoints/              # Auth, plots, crop cycles, drone, pest, soil
└── tests/                          # 11 unit & integration tests
```

---

## 🚀 Quick Start

### 1. Run with Python Virtual Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd agri-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env

# Run FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Access the Application

- **Web Frontend**: [http://127.0.0.1:8000/app](http://127.0.0.1:8000/app)
- **Interactive API Docs (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **System Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 3. Run with Docker Compose

```bash
docker-compose up -d --build
```

This starts:
- PostgreSQL 16 with PostGIS 3.4 on port 5432
- Redis on port 6379
- FastAPI backend on port 8000

---

## 🧪 Running Tests

```bash
pytest
```

All 11 unit tests cover:
- Agronomy calculation with STCR adjustments
- Weather hold-off safety rules
- Drone orthomosaic patch classification
- CIBRC pest thresholds & DGCA drone spray parameter generation
- GeoJSON boundary polygon validation and area calculations
- Soil Health Card nearest-neighbor fallback
# AgriAssist
this an application for farmers assistance with modern technology
 3e4816d85e1bc932d2199ea6ccc0fca6a3e6540a
