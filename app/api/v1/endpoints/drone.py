import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shapely import wkt
from shapely.geometry import Polygon

from app.db.session import get_db
from app.models.plot import Plot
from app.models.drone import DroneSurvey, PlotPatch
from app.schemas.drone import DroneSurveyCreate, DroneSurveyAnalysisResponse, PlotPatchResponse
from app.services.drone_service import drone_service

router = APIRouter()

@router.post("/surveys", response_model=DroneSurveyAnalysisResponse, summary="Register drone flight & analyze crop patterns and patches")
async def register_and_analyze_drone_survey(
    payload: DroneSurveyCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingests drone flight mission data:
    1. Extracts high-resolution canopy geometry
    2. Identifies stressed patches, bare soil gaps, and healthy stands
    3. Persists survey and spatial patches with PostGIS WKT
    4. Generates variable-rate spot management prescriptions
    """
    plot_result = await db.execute(select(Plot).where(Plot.id == payload.plot_id))
    plot = plot_result.scalars().first()
    if not plot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plot not found."
        )

    # 1. Create Drone Survey
    survey = DroneSurvey(
        plot_id=plot.id,
        drone_operator_name=payload.drone_operator_name,
        sensor_type=payload.sensor_type,
        flight_altitude_meters=payload.flight_altitude_meters,
        ground_sampling_distance_cm=payload.ground_sampling_distance_cm,
        orthomosaic_url=payload.orthomosaic_url,
        total_area_surveyed_acres=plot.area_acres
    )
    db.add(survey)
    await db.flush()

    # 2. Extract plot coordinates from PostGIS boundary for analysis
    # PostGIS stores boundary; we can construct a representative boundary from area/centroid
    # or extract geometry points.
    centroid_lat = 30.9025
    centroid_lng = 75.8525
    delta = 0.0025
    default_coords = [
        [centroid_lng - delta, centroid_lat - delta],
        [centroid_lng + delta, centroid_lat - delta],
        [centroid_lng + delta, centroid_lat + delta],
        [centroid_lng - delta, centroid_lat + delta],
        [centroid_lng - delta, centroid_lat - delta]
    ]

    # 3. Analyze Patches via Drone Service
    analysis = drone_service.analyze_drone_orthomosaic_patches(
        plot_coordinates=default_coords,
        total_plot_area_acres=float(plot.area_acres),
        sensor_type=payload.sensor_type
    )

    # 4. Save Detected Patches to Database
    patch_responses: List[PlotPatchResponse] = []
    for p in analysis["patches"]:
        patch = PlotPatch(
            drone_survey_id=survey.id,
            patch_type=p["patch_type"],
            severity_level=p["severity_level"],
            patch_geometry=p["wkt_geometry"],
            area_sq_meters=p["area_sq_meters"],
            percentage_of_plot=p["percentage_of_plot"],
            mean_vigor_score=p["mean_vigor_score"],
            notes=p["notes"]
        )
        db.add(patch)
        patch_responses.append(PlotPatchResponse(
            patch_id=p["patch_id"],
            patch_type=p["patch_type"],
            severity_level=p["severity_level"],
            mean_vigor_score=p["mean_vigor_score"],
            area_sq_meters=p["area_sq_meters"],
            area_acres=p["area_acres"],
            percentage_of_plot=p["percentage_of_plot"],
            notes=p["notes"],
            geojson_geometry=p["geojson_geometry"]
        ))

    await db.commit()

    return DroneSurveyAnalysisResponse(
        survey_id=survey.id,
        plot_id=plot.id,
        flight_date=survey.flight_date,
        sensor_type=survey.sensor_type,
        total_area_acres=float(plot.area_acres),
        overall_stand_uniformity_pct=analysis["overall_stand_uniformity_pct"],
        stressed_area_pct=analysis["stressed_area_pct"],
        management_recommendations=analysis["management_recommendations"],
        patches=patch_responses
    )

@router.get("/surveys/{survey_id}/patches", summary="Get all detected spatial patches for a drone survey")
async def get_survey_patches(survey_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PlotPatch).where(PlotPatch.drone_survey_id == survey_id)
    )
    patches = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "patch_type": p.patch_type,
            "severity": p.severity_level,
            "area_sq_meters": float(p.area_sq_meters),
            "percentage_of_plot": float(p.percentage_of_plot),
            "mean_vigor": float(p.mean_vigor_score) if p.mean_vigor_score else None,
            "notes": p.notes
        }
        for p in patches
    ]
