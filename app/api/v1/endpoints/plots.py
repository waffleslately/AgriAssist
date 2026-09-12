import uuid
import math
from datetime import date
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shapely.geometry import Polygon

from app.db.session import get_db
from app.models.farmer import Farmer
from app.models.plot import Plot
from app.models.crop_cycle import CropCycle
from app.models.drone import DroneScan
from app.models.satellite_observation import SatelliteObservation
from app.models.advisory import Advisory
from app.schemas.plot import PlotOnboardRequest, PlotResponse

from app.services import gee_service, weather_service, soil_service, agronomy_engine, localization_service
from app.api.v1.endpoints.auth import FARMER_STORE

router = APIRouter()

def calculate_geodesic_area_acres(coords: List[List[float]]) -> float:
    """
    Calculate geodesic area of WGS84 polygon in acres using the authalic sphere formula.
    Pure Python implementation, robust across all platforms without DLL dependencies.
    """
    if len(coords) < 3:
        return 0.1
    R = 6371007.2
    total = 0.0
    n = len(coords)
    
    for i in range(n - 1):
        p1 = coords[i]
        p2 = coords[i + 1]
        lon1 = math.radians(p1[0])
        lat1 = math.radians(p1[1])
        lon2 = math.radians(p2[0])
        lat2 = math.radians(p2[1])
        total += (lon2 - lon1) * (2.0 + math.sin(lat1) + math.sin(lat2))
    
    area_sq_m = abs(total * (R * R) / 2.0)
    acres = area_sq_m * 0.000247105
    return round(max(0.1, acres), 2)

@router.post("/onboard", summary="Vertical Slice: Onboard Plot -> Fetch Satellite & Soil -> Generate Advisory")
async def onboard_plot_pipeline(
    payload: PlotOnboardRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Complete end-to-end vertical slice with dynamic weather & manual override support.
    Resilient fallback: runs seamlessly with or without live PostgreSQL.
    """
    coords = payload.boundary.coordinates[0]
    shapely_poly = Polygon(coords)
    if not shapely_poly.is_valid:
        shapely_poly = shapely_poly.buffer(0)

    area_acres = calculate_geodesic_area_acres(coords)
    centroid = shapely_poly.centroid
    lat, lng = centroid.y, centroid.x

    plot_id = uuid.uuid4()
    crop_cycle_id = uuid.uuid4()
    farmer_id = uuid.uuid4()

    # Try saving to PostgreSQL/PostGIS if DB is available
    has_db = False
    try:
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
        has_db = True
        plot_id = plot.id
        crop_cycle_id = crop_cycle.id
    except Exception:
        # PostgreSQL offline -> use memory repository
        pass

    # 4. Fetch Nearest Soil Health Sample (or district benchmark)
    soil_data = await soil_service.get_nearest_soil_sample(
        db=db if has_db else None,
        lat=lat,
        lng=lng,
        state=payload.state,
        district=payload.district
    )

    # Apply Manual Soil Overrides if provided by farmer
    if payload.manual_override_enabled:
        if payload.manual_soil_n is not None:
            soil_data["available_nitrogen_kg_ha"] = float(payload.manual_soil_n)
        if payload.manual_soil_p is not None:
            soil_data["available_phosphorus_kg_ha"] = float(payload.manual_soil_p)
        if payload.manual_soil_k is not None:
            soil_data["available_potassium_kg_ha"] = float(payload.manual_soil_k)
        if payload.manual_soil_ph is not None:
            soil_data["ph"] = float(payload.manual_soil_ph)
        if payload.manual_soil_oc is not None:
            soil_data["organic_carbon_pct"] = float(payload.manual_soil_oc)
        soil_data["source"] = "Farmer Ground Test (Manual Input)"

    # 5. Fetch Satellite Metrics (GEE Sentinel-2) + 60-day NDVI Timeseries
    sat_data = await gee_service.get_plot_metrics(
        coordinates=coords,
        target_date=date.today()
    )
    ndvi_timeseries = await gee_service.get_ndvi_timeseries(coordinates=coords, days=60)

    # 6. Fetch Weather Forecast (Open-Meteo)
    weather_data = await weather_service.get_forecast(latitude=lat, longitude=lng)

    # Apply Manual Weather/Rain Gauge Overrides if provided by farmer
    if payload.manual_override_enabled and payload.manual_rain_48h_mm is not None:
        weather_data["precipitation_48h_mm"] = float(payload.manual_rain_48h_mm)
        weather_data["heavy_rain_warning"] = float(payload.manual_rain_48h_mm) > 15.0
        weather_data["source"] = "Farmer Rain Gauge (Manual Observation)"

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

    # Persist in-memory farmer profile plots
    phone = payload.phone_number.strip().replace("+91", "").replace(" ", "")
    if phone in FARMER_STORE:
        plot_entry = {
            "plot_id": str(plot_id),
            "plot_name": payload.plot_name,
            "crop_name": payload.crop_name,
            "area_acres": area_acres,
            "sowing_date": str(payload.sowing_date),
            "stage": plan["crop_stage"],
            "mean_ndvi": sat_data.get("mean_ndvi", 0.55),
            "centroid": {"lat": round(lat, 5), "lng": round(lng, 5)},
            "coordinates": coords
        }
        # Avoid duplicate plot names (update if same name, else append as new plot)
        FARMER_STORE[phone]["plots"] = [
            p for p in FARMER_STORE[phone]["plots"] if p.get("plot_name") != payload.plot_name
        ]
        FARMER_STORE[phone]["plots"].append(plot_entry)

    if has_db:
        try:
            obs = SatelliteObservation(
                plot_id=plot_id,
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
            advisory = Advisory(
                crop_cycle_id=crop_cycle_id,
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
        except Exception:
            pass

    return {
        "status": "success",
        "plot": {
            "id": str(plot_id),
            "name": payload.plot_name,
            "area_acres": area_acres,
            "centroid": {"lat": round(lat, 5), "lng": round(lng, 5)}
        },
        "crop": {
            "crop_cycle_id": str(crop_cycle_id),
            "crop_name": payload.crop_name,
            "stage": plan["crop_stage"],
            "days_after_sowing": plan["days_after_sowing"]
        },
        "soil_profile": soil_data,
        "satellite": {
            **sat_data,
            "ndvi_timeseries": ndvi_timeseries
        },
        "weather": {
            "max_temp": weather_data.get("max_temp"),
            "min_temp": weather_data.get("min_temp"),
            "precipitation_48h_mm": weather_data.get("precipitation_48h_mm"),
            "heavy_rain_warning": weather_data.get("heavy_rain_warning"),
            "source": weather_data.get("source", "Open-Meteo Live API"),
            "forecast_dates": weather_data.get("dates", [])[:7],
            "forecast_precip_mm": weather_data.get("raw_daily", {}).get("precipitation_sum", [])[:7],
            "forecast_max_temp": weather_data.get("raw_daily", {}).get("temperature_2m_max", [])[:7],
            "forecast_min_temp": weather_data.get("raw_daily", {}).get("temperature_2m_min", [])[:7]
        },
        "recommendation": {
            "fertilizer_schedule": plan["fertilizer_schedule"],
            "irrigation_advice": plan["irrigation_advice"],
            "weather_warning": plan.get("weather_hold_warning"),
            "localized_text": localized.get(payload.language, localized["en"]),
            "localized_hi": localized.get("hi"),
            "localized_en": localized.get("en"),
            "localized_pa": localized.get("pa"),
            "localized_mr": localized.get("mr")
        }
    }


@router.get("/{plot_id}/development-history", summary="Crop Development Over Time — aggregated NDVI & health trend across past drone scans")
async def get_plot_development_history(plot_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Aggregates all past drone scans for this plot into a vegetation trend.
    For each scan, computes:
      - avg_ndvi: mean NDVI across all cells in result_json
      - healthy_pct / moderate_pct / stressed_pct: % of cells in each category
      - weed_count: number of weed cluster points
    Returns an ordered list of scan summaries (oldest → newest) for charting.
    No new computation — pure aggregation over already-stored result_json data.
    """
    # Look up crop name from most recent active crop cycle for this plot
    crop_name = "Unknown"
    plot_name = "Field"
    try:
        plot_res = await db.execute(select(Plot).where(Plot.id == plot_id))
        plot = plot_res.scalars().first()
        if plot:
            plot_name = plot.name or "Field"

        cycle_res = await db.execute(
            select(CropCycle)
            .where(CropCycle.plot_id == plot_id, CropCycle.is_active == True)
            .order_by(CropCycle.sowing_date.desc())
        )
        cycle = cycle_res.scalars().first()
        if cycle:
            crop_name = cycle.crop_name
    except Exception:
        pass

    # Fetch all scans for this plot, oldest first for trend chart ordering
    try:
        stmt = (
            select(DroneScan)
            .where(DroneScan.plot_id == plot_id)
            .order_by(DroneScan.scan_date.asc())
        )
        result = await db.execute(stmt)
        scans = result.scalars().all()
    except Exception as e:
        scans = []

    # Fallback to in-memory store if DB is offline or empty
    if not scans:
        from app.api.v1.endpoints.drone import DRONE_SCANS_STORE
        mem_list = DRONE_SCANS_STORE.get(str(plot_id), [])
        # Sort oldest first by scan_date
        scans = sorted(mem_list, key=lambda s: s["scan_date"])

    scan_trend = []
    for s in scans:
        if isinstance(s, dict):
            scan_id = str(s["id"])
            s_date = s["scan_date"]
            grid = s.get("result_json") or {}
        else:
            scan_id = str(s.id)
            s_date = s.scan_date
            grid = s.result_json or {}

        scan_date_str = s_date.strftime("%Y-%m-%d") if hasattr(s_date, "strftime") else str(s_date).split("T")[0]

        healthy_cells = grid.get("healthy", [])
        moderate_cells = grid.get("moderate", [])
        stressed_cells = grid.get("stressed_or_bare", [])
        weed_points = grid.get("weed_cluster", []) or grid.get("weed_detections", [])

        all_cells = grid.get("cells", [])
        if not all_cells:
            all_cells = healthy_cells + moderate_cells + stressed_cells
        else:
            if not healthy_cells:
                healthy_cells = [c for c in all_cells if c.get("status") == "healthy"]
            if not moderate_cells:
                moderate_cells = [c for c in all_cells if c.get("status") == "moderate"]
            if not stressed_cells:
                stressed_cells = [c for c in all_cells if c.get("status") == "stressed_or_bare"]

        total_cells = len(healthy_cells) + len(moderate_cells) + len(stressed_cells)

        # avg_ndvi: mean over all cells that carry an ndvi value
        ndvi_values = [c.get("ndvi") for c in all_cells if c.get("ndvi") is not None]
        avg_ndvi = round(sum(ndvi_values) / len(ndvi_values), 3) if ndvi_values else None

        healthy_pct = round(len(healthy_cells) / total_cells * 100, 1) if total_cells else 0.0
        moderate_pct = round(len(moderate_cells) / total_cells * 100, 1) if total_cells else 0.0
        stressed_pct = round(len(stressed_cells) / total_cells * 100, 1) if total_cells else 0.0

        # Normalise to exactly 100%
        total_pct = healthy_pct + moderate_pct + stressed_pct
        if total_pct > 0 and abs(total_pct - 100.0) > 0.5:
            scale = 100.0 / total_pct
            healthy_pct = round(healthy_pct * scale, 1)
            moderate_pct = round(moderate_pct * scale, 1)
            stressed_pct = round(100.0 - healthy_pct - moderate_pct, 1)

        scan_trend.append({
            "scan_id": scan_id,
            "scan_date": scan_date_str,
            "avg_ndvi": avg_ndvi,
            "healthy_pct": healthy_pct,
            "moderate_pct": moderate_pct,
            "stressed_pct": stressed_pct,
            "weed_count": len(weed_points),
            "total_cells": total_cells,
            "image_url": grid.get("image_url")
        })

    return {
        "plot_id": str(plot_id),
        "plot_name": plot_name,
        "crop": crop_name,
        "scan_count": len(scan_trend),
        "scans": scan_trend
    }
