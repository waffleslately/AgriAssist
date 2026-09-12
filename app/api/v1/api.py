from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    farmers,
    plots,
    crop_cycles,
    satellite,
    soil,
    advisories,
    drone,
    pest,
    iot,
    livestock,
    soil_reports
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & OTP"])
api_router.include_router(farmers.router, prefix="/farmers", tags=["Farmers Profile"])
api_router.include_router(plots.router, prefix="/plots", tags=["Plots & Onboarding"])
api_router.include_router(crop_cycles.router, prefix="/crop-cycles", tags=["Crop Cycles"])
api_router.include_router(satellite.router, prefix="/satellite", tags=["Satellite Analytics"])
api_router.include_router(soil.router, prefix="/soil", tags=["Soil Health & Benchmarks"])
api_router.include_router(soil_reports.router, prefix="/soil-reports", tags=["Soil Reports & Recommender"])
api_router.include_router(advisories.router, prefix="/advisories", tags=["Advisories & Recommendations"])
api_router.include_router(drone.router, prefix="/drone", tags=["Drone Surveys & Patch Analytics"])
api_router.include_router(pest.router, prefix="/pest", tags=["Pest Control & Drone Spraying"])
api_router.include_router(iot.router, prefix="/iot", tags=["IoT Telemetry & Collar Ingestion"])
api_router.include_router(livestock.router, prefix="/livestock", tags=["Livestock Tracking & Grazing Analytics"])

