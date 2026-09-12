import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.plot import Plot
from app.models.crop_cycle import CropCycle
from app.models.pest_control import PestDetectionReport
from app.schemas.pest import PestDiagnoseRequest, PestReportResponse
from app.services.pest_control_engine import pest_control_engine
from app.seeds.pest_cibrc_guidelines import PEST_CIBRC_GUIDELINES

router = APIRouter()

@router.post("/diagnose", response_model=PestReportResponse, summary="Diagnose pest/disease & generate IPM + Drone Spray Prescription")
async def diagnose_pest(
    payload: PestDiagnoseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    1. Diagnoses pest based on observed symptoms or scouting count
    2. Evaluates Economic Threshold Level (ETL)
    3. Prescribes CIBRC-registered biological & chemical controls
    4. Generates DGCA-compliant Drone Spraying Parameters (10 L/acre ULV)
    5. Returns bilingual English & Hindi advice cards
    """
    plot_result = await db.execute(select(Plot).where(Plot.id == payload.plot_id))
    plot = plot_result.scalars().first()
    if not plot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plot not found."
        )

    # 1. Run Pest Control Engine
    diag = pest_control_engine.diagnose_and_prescribe(
        crop_name=payload.crop_name,
        pest_key=payload.pest_key,
        severity_observed_pct=payload.severity_observed_pct,
        area_acres=float(plot.area_acres),
        drone_spray_requested=payload.drone_spray_requested
    )

    # 2. Persist Report
    report = PestDetectionReport(
        plot_id=plot.id,
        crop_cycle_id=payload.crop_cycle_id,
        drone_survey_id=payload.drone_survey_id,
        detection_source="drone_spectral" if payload.drone_survey_id else "field_scouting",
        pest_or_disease_name=diag["pest_name"],
        scientific_name=diag.get("scientific_name"),
        severity_score=payload.severity_observed_pct / 100.0,
        economic_threshold_breached=diag["economic_threshold_breached"],
        prescribed_ipm_measures=diag["ipm_measures"],
        drone_spray_prescription=diag["drone_spray_prescription"],
        localized_advice=diag["localized_advice"]
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return PestReportResponse(
        id=report.id,
        crop=diag["crop"],
        pest_name=diag["pest_name"],
        scientific_name=diag.get("scientific_name"),
        severity_observed_pct=diag["severity_observed_pct"],
        economic_threshold_breached=diag["economic_threshold_breached"],
        etl_guideline=diag["etl_guideline"],
        ipm_measures=diag["ipm_measures"],
        drone_spray_prescription=diag["drone_spray_prescription"],
        localized_advice=diag["localized_advice"]
    )

@router.get("/guidelines/{crop_name}", summary="Get CIBRC registered pests and controls for a crop")
async def get_crop_pest_guidelines(crop_name: str):
    crop = crop_name.lower().strip()
    data = PEST_CIBRC_GUIDELINES.get(crop)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guidelines for crop '{crop_name}' not found. Supported: {list(PEST_CIBRC_GUIDELINES.keys())}"
        )
    return data
