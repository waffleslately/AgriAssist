import uuid
import math
from datetime import date
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shapely.geometry import Polygon

from app.db.session import get_db
from app.models.farmer import Farmer
from app.models.plot import Plot
from app.models.crop_cycle import CropCycle
from app.models.satellite_observation import SatelliteObservation
from app.models.advisory import Advisory
from app.schemas.plot import PlotOnboardRequest, PlotResponse
from app.services import gee_service, weather_service, soil_service, agronomy_engine, localization_service

router = APIRouter()

def calculate_geodesic_area_acres(coords: List[List[float]]) -> float:
    """
    Calculate geodesic area of WGS84 polygon in acres using the authalic sphere formula.
    Pure Python implementation, robust across all platforms without DLL dependencies.
    """
    if len(coords) < 3:
        return 0.1
    # Authalic Earth radius in meters
    R = 6371007.2
    total = 0.0
    n = len(coords)
    
    # Ring coordinates: [lng, lat]
    for i in range(n - 1):
        p1 = coords[i]
        p2 = coords[i + 1]
        lon1 = math.radians(p1[0])
        lat1 = math.radians(p1[1])
        lon2 = math.radians(p2[0])
        lat2 = math.radians(p2[1])
        total += (lon2 - lon1) * (2.0 + math.sin(lat1) + math.sin(lat2))
    
    area_sq_m = abs(total * (R * R) / 2.0)
    # 1 square meter = 0.000247105 acres
    acres = area_sq_m * 0.000247105
    return round(max(0.1, acres), 2)

@router.post("/onboard", summary="Vertical Slice: Onboard Plot -> Fetch Satellite & Soil -> Generate Advisory")
async def onboard_plot_pipeline(
    payload: PlotOnboardRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Complete end-to-end vertical slice:
    1. Validates plot polygon & computes acreage
    2. Registers farmer & plot in PostGIS
    3. Fetches nearest Soil Health Card metrics
    4. Fetches Sentinel-2 NDVI & moisture via GEE
    5. Checks 7-day weather forecast (rainfall warnings)
    6. Generates ICAR-aligned fertilizer plan in standard bags (Urea, DAP, MOP)
    7. Returns localized advisory card (Hindi / English)
    """
    coords = payload.boundary.coordinates[0]
    shapely_poly = Polygon(coords)
    if not shapely_poly.is_valid:
        shapely_poly = shapely_poly.buffer(0)

    area_acres = calculate_geodesic_area_acres(coords)
    centroid = shapely_poly.centroid
    lat, lng = centroid.y, centroid.x

    # 1. Upsert Farmer
    result = await db.execute(
        select(Farmer).where(Farmer.phone_number == payload.phone_number)
    )
    farmer = result.scalars().first()
    if not farmer:
        farmer = Farmer(
            phone_number=payload.phone_number,
            name=payload.farmer_name,
            preferred_language=payload.language,
            state=payload.state,
            district=payload.district,
            sub_district=payload.sub_district,
            village=payload.village
        )
        db.add(farmer)
        await db.flush()

    # 2. Persist Plot with PostGIS WKT
    wkt_poly = f"SRID=4326;{shapely_poly.wkt}"
    wkt_centroid = f"SRID=4326;POINT({lng} {lat})"

    plot = Plot(
        farmer_id=farmer.id,
        name=payload.plot_name,
        boundary=wkt_poly,
        centroid=wkt_centroid,
        area_acres=area_acres,
        soil_texture=payload.soil_texture,
        irrigation_source=payload.irrigation_source
    )
    db.add(plot)
    await db.flush()

    # 3. Create Crop Cycle
    crop_cycle = CropCycle(
        plot_id=plot.id,
        crop_name=payload.crop_name,
        variety=payload.variety,
        season=payload.season,
        sowing_date=payload.sowing_date,
        target_yield_quintal_per_acre=payload.target_yield_quintal_per_acre,
        is_active=True
    )
    db.add(crop_cycle)
    await db.flush()

    # 4. Fetch Nearest Soil Health Sample (or district benchmark)
    soil_data = await soil_service.get_nearest_soil_sample(
        db=db,
        lat=lat,
        lng=lng,
        state=payload.state,
        district=payload.district
    )

    # 5. Fetch Satellite Metrics (GEE Sentinel-2)
    sat_data = await gee_service.get_plot_metrics(
        coordinates=coords,
        target_date=date.today()
    )

    # Persist Observation
    obs = SatelliteObservation(
        plot_id=plot.id,
        satellite_source=sat_data.get("source", "Sentinel-2"),
        acquisition_date=date.today(),
        mean_ndvi=sat_data.get("mean_ndvi", 0.55),
        p10_ndvi=sat_data.get("p10_ndvi"),
        p90_ndvi=sat_data.get("p90_ndvi"),
        soil_moisture_proxy=sat_data.get("soil_moisture_proxy"),
        cloud_cover_percentage=sat_data.get("cloud_cover_percentage", 0.0),
        raw_metrics=sat_data
    )
    db.add(obs)

    # 6. Fetch Weather Forecast
    weather_data = await weather_service.get_forecast(latitude=lat, longitude=lng)

    # 7. Compute Agronomy Recommendation
    plan = agronomy_engine.calculate_plan(
        crop_name=payload.crop_name,
        sowing_date=payload.sowing_date,
        soil_metrics=soil_data,
        satellite_metrics=sat_data,
        weather_metrics=weather_data,
        area_acres=area_acres
    )

    # 8. Localize Advisory
    localized = localization_service.generate_localized_advisory(
        plan=plan,
        language=payload.language
    )

    # 9. Persist Advisory
    advisory = Advisory(
        crop_cycle_id=crop_cycle.id,
        trigger_source="onboarding",
        crop_stage=plan["crop_stage"],
        fertilizer_plan=plan,
        irrigation_advice=plan["irrigation_advice"],
        weather_summary=weather_data,
        localized_message=localized,
        is_sent=True
    )
    db.add(advisory)
    await db.commit()

    return {
        "status": "success",
        "plot": {
            "id": str(plot.id),
            "name": plot.name,
            "area_acres": area_acres,
            "centroid": {"lat": round(lat, 5), "lng": round(lng, 5)}
        },
        "crop": {
            "crop_cycle_id": str(crop_cycle.id),
            "crop_name": payload.crop_name,
            "stage": plan["crop_stage"],
            "days_after_sowing": plan["days_after_sowing"]
        },
        "soil_profile": soil_data,
        "satellite": sat_data,
        "weather": {
            "max_temp": weather_data.get("max_temp"),
            "min_temp": weather_data.get("min_temp"),
            "precipitation_48h_mm": weather_data.get("precipitation_48h_mm"),
            "heavy_rain_warning": weather_data.get("heavy_rain_warning")
        },
        "recommendation": {
            "fertilizer_schedule": plan["fertilizer_schedule"],
            "irrigation_advice": plan["irrigation_advice"],
            "weather_warning": plan.get("weather_hold_warning"),
            "localized_text": localized.get(payload.language, localized["en"])
        }
    }
