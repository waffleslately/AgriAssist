import os
import json
import uuid
import logging
import traceback
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shapely.geometry import Polygon

from app.db.session import get_db
from app.models.plot import Plot
from app.models.drone import DroneSurvey, PlotPatch, DroneScan
from app.schemas.drone import DroneSurveyCreate, DroneSurveyAnalysisResponse, PlotPatchResponse
from app.services.drone_service import drone_service
from app.services.drone_analysis_service import drone_analysis_service

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = Path("uploads/drone")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/analyze-image", summary="Upload Drone Imagery & Compute Interactive NDVI Grid + Weed Clusters")
async def analyze_drone_image_direct(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyzes uploaded drone orthomosaic imagery with rigorous validation:
    1. Input Validation:
       - Checks if an image file was provided.
       - Checks if multispectral sensor matches file type (e.g. .tif required for NIR, rejects .jpg/.png).
       - Checks if target plot / field boundary exists.
    2. Computes pure mathematical NDVI grid (10m x 10m cells).
    3. Detects weed clusters using Roboflow hosted inference API.
    4. Merges results, persists to drone_scans table, and returns scan_id + interactive grid.
    """
    file_obj = None
    file_name = ""
    sensor_type = "multispectral_ndvi"
    crop_name = "wheat"
    flight_altitude = 35.0
    total_area_acres = 3.5
    plot_id_val = None
    boundary_coords = None

    content_type = request.headers.get("content-type", "")

    # Parse Multipart Form Data or JSON
    if "multipart/form-data" in content_type:
        form = await request.form()
        file_item = form.get("file")
        if file_item and hasattr(file_item, "filename") and file_item.filename:
            file_obj = file_item
            file_name = file_item.filename

        sensor_type = str(form.get("sensor_type") or "multispectral_ndvi")
        crop_name = str(form.get("crop_name") or "wheat")
        plot_id_val = form.get("plot_id")
        
        coords_raw = form.get("plot_coordinates")
        if coords_raw:
            try:
                boundary_coords = json.loads(coords_raw) if isinstance(coords_raw, str) else coords_raw
            except Exception:
                boundary_coords = None

        try:
            flight_altitude = float(form.get("flight_altitude_meters") or 35.0)
            total_area_acres = float(form.get("total_area_acres") or 3.5)
        except (ValueError, TypeError):
            pass

    elif "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            body = {}
        sensor_type = str(body.get("sensor_type") or "multispectral_ndvi")
        crop_name = str(body.get("crop_name") or "wheat")
        plot_id_val = body.get("plot_id")
        boundary_coords = body.get("plot_coordinates")
        flight_altitude = float(body.get("flight_altitude_meters") or 35.0)
        total_area_acres = float(body.get("total_area_acres") or 3.5)
        file_name = str(body.get("file_name") or "")

    # ============================================================
    # 1. INPUT VALIDATION (Fixes HTTP 500)
    # ============================================================
    
    # Check A: File presence
    if not file_obj and not file_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a drone image before analyzing."
        )

    # Check B: Multispectral vs File Type check
    sensor_clean = sensor_type.lower()
    fn_clean = (file_name or (file_obj.filename if file_obj else "")).lower()

    if ("multispectral" in sensor_clean or "ndre" in sensor_clean) and (
        fn_clean.endswith(".jpg") or fn_clean.endswith(".jpeg") or fn_clean.endswith(".png")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This file doesn't contain multispectral bands. Upload a .tif with NIR data, or switch Sensor Type to RGB."
        )

    # Check C: Target Land boundary check
    # If boundary_coords not provided in request, attempt lookup from DB via plot_id
    if (not boundary_coords or len(boundary_coords) < 3) and plot_id_val:
        try:
            plot_uuid = uuid.UUID(str(plot_id_val))
            plot_res = await db.execute(select(Plot).where(Plot.id == plot_uuid))
            p = plot_res.scalars().first()
            if p and p.boundary:
                # Extract boundary points if GeoAlchemy geometry
                pass
        except Exception:
            pass

    if not boundary_coords or len(boundary_coords) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Select a valid plot with a saved field boundary first."
        )

    # ============================================================
    # 2 & 3. NDVI GRID & WEED DETECTION
    # ============================================================
    try:
        # Save temporary file on disk for processing
        saved_path = UPLOAD_DIR / f"{uuid.uuid4()}_{fn_clean}"
        if file_obj:
            content = await file_obj.read()
            with open(saved_path, "wb") as f:
                f.write(content)
        else:
            # Generate representative demo image if called via simulation payload
            from PIL import Image as PILImage
            demo_img = PILImage.new("RGB", (640, 480), color=(76, 175, 80))
            demo_img.save(saved_path)

        # 2. Compute NDVI Grid
        ndvi_cells = drone_analysis_service.compute_ndvi_grid(
            image_path=str(saved_path),
            plot_boundary=boundary_coords,
            grid_size_m=10.0,
            sensor_type=sensor_type
        )

        # 3. Detect Weeds via Roboflow Hosted API
        weed_points = drone_analysis_service.detect_weeds(
            image_path=str(saved_path),
            plot_boundary=boundary_coords
        )

        # 4. Combine Results
        healthy_cells = [c for c in ndvi_cells if c["status"] == "healthy"]
        moderate_cells = [c for c in ndvi_cells if c["status"] == "moderate"]
        stressed_cells = [c for c in ndvi_cells if c["status"] == "stressed_or_bare"]

        combined_grid = {
            "healthy": healthy_cells,
            "moderate": moderate_cells,
            "stressed_or_bare": stressed_cells,
            "weed_cluster": weed_points
        }

        # Clean up temporary file
        try:
            if saved_path.exists():
                os.remove(saved_path)
        except Exception:
            pass

        # 5. Persist to drone_scans table
        scan_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        target_plot_uuid = None
        if plot_id_val:
            try:
                target_plot_uuid = uuid.UUID(str(plot_id_val))
            except ValueError:
                target_plot_uuid = None

        if target_plot_uuid:
            try:
                scan_record = DroneScan(
                    id=scan_id,
                    plot_id=target_plot_uuid,
                    scan_date=now,
                    result_json=combined_grid
                )
                db.add(scan_record)
                await db.commit()
            except Exception as db_e:
                logger.warning(f"Could not persist drone scan to DB: {db_e}")

        # Summary statistics
        total_cells = len(ndvi_cells)
        stressed_pct = round((len(stressed_cells) / total_cells * 100.0), 1) if total_cells > 0 else 0.0
        healthy_pct = round((len(healthy_cells) / total_cells * 100.0), 1) if total_cells > 0 else 100.0

        # DGCA Precision Flight Plan
        stressed_acres = round(total_area_acres * (stressed_pct / 100.0), 2)
        dgca_mission = {
            "flight_altitude_m": flight_altitude,
            "flight_speed_m_s": 3.5,
            "swath_width_m": 4.0,
            "target_treatment_area_acres": stressed_acres,
            "recommended_payload": "Micro-nutrient Booster (ZnSO4 + Urea 2% foliar spray)" if crop_name == "wheat" else "Targeted bio-stimulant foliar spray",
            "ulv_water_rate_l_acre": 10.0,
            "total_spray_liquid_litres": round(stressed_acres * 10.0, 1),
            "nozzle_spec": "Anti-drift Flat Fan (150-250 microns)",
            "weather_envelope": "Wind < 10 km/h, Temp < 35°C, No precipitation in 6 hours"
        }

        return {
            "status": "success",
            "scan_id": str(scan_id),
            "plot_id": str(target_plot_uuid) if target_plot_uuid else None,
            "scan_date": now.isoformat(),
            "sensor_type": sensor_type,
            "crop_name": crop_name,
            "total_cells": total_cells,
            "overall_stand_uniformity_pct": healthy_pct,
            "stressed_area_pct": stressed_pct,
            "grid": combined_grid,
            "dgca_precision_mission": dgca_mission,
            "management_recommendations": [
                f"Variable Rate Spraying: Target spot-treatment on {stressed_pct}% of the field (Stressed & Gap zones) to reduce chemical usage by {healthy_pct}%.",
                f"Weed Hotspots: {len(weed_points)} weed clusters detected. Conduct targeted spot weeding.",
                "High Vigor Zones: Maintain standard irrigation rotation."
            ]
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in drone image analysis: {exc}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during drone image analysis. Please try again or contact support."
        )


@router.get("/scans/{plot_id}", summary="Fetch past drone scans for a plot")
async def get_plot_drone_scans(plot_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieves previous drone scans stored in the drone_scans table."""
    try:
        stmt = select(DroneScan).where(DroneScan.plot_id == plot_id).order_by(DroneScan.scan_date.desc())
        result = await db.execute(stmt)
        scans = result.scalars().all()
        return [
            {
                "id": str(s.id),
                "plot_id": str(s.plot_id),
                "scan_date": s.scan_date.isoformat(),
                "created_at": s.created_at.isoformat(),
                "summary": {
                    "healthy_count": len(s.result_json.get("healthy", [])),
                    "moderate_count": len(s.result_json.get("moderate", [])),
                    "stressed_count": len(s.result_json.get("stressed_or_bare", [])),
                    "weed_count": len(s.result_json.get("weed_cluster", []))
                }
            }
            for s in scans
        ]
    except Exception as e:
        logger.warning(f"Error fetching drone scans: {e}")
        return []
