import os
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.plot import Plot
from app.models.pest_reference import (
    PestReference,
    PestDiagnosis,
    PEST_REFERENCE_STORE,
    PEST_DIAGNOSES_STORE
)
from app.seeds.pest_reference_data import (
    PEST_REFERENCE_DATA,
    GENERIC_COUNTERMEASURES,
    find_pest_reference
)
from app.services.pest_detection_service import pest_detection_service
from app.services.pest_control_engine import pest_control_engine
from app.seeds.pest_cibrc_guidelines import DGCA_DRONE_SPRAY_SOP

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = Path("uploads/pest")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class ManualPestSelectPayload(BaseModel):
    pest_name: str
    crop_hint: Optional[str] = None
    plot_id: Optional[str] = None
    severity_observed_pct: Optional[float] = 18.0
    drone_spray_requested: Optional[bool] = True


@router.post("/analyze", summary="Analyze Photo for Pest/Disease Diagnosis & Attach ICAR Countermeasures")
async def analyze_pest_photo(
    request: Request,
    photo: Optional[UploadFile] = File(None),
    plot_id: Optional[str] = Form(None),
    suspected_pest: Optional[str] = Form(None),
    crop_hint: Optional[str] = Form(None),
    severity_observed_pct: Optional[float] = Form(None),
    drone_spray_requested: Optional[bool] = Form(True),
    db: AsyncSession = Depends(get_db)
):
    """
    POST /pest-diagnosis/analyze
    1. Validates real image file (jpg/jpeg/png) with clean 400 error (matches drone-image upload pattern).
    2. Executes pretrained vision models (Roboflow Universe / Hugging Face / visual signatures).
    3. Looks up detected pest in ICAR pest_reference table.
    4. Handles low confidence (<60%) by returning top candidate matches with uncertainty banner.
    5. Falls back to generic IPM advice if unclassified.
    6. Attaches DGCA Ultra-Low Volume drone spray prescription using active chemical ingredient.
    7. Persists diagnosis to pest_diagnoses table and in-memory store.
    """
    # 1. Image Validation
    if not photo or not photo.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No photo provided. Please upload a clear photo (.jpg or .png) of the affected crop."
        )

    fn_clean = photo.filename.lower()
    if not (fn_clean.endswith(".jpg") or fn_clean.endswith(".jpeg") or fn_clean.endswith(".png")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: '{photo.filename}'. Allowed formats: JPG, JPEG, PNG."
        )

    # Save to disk
    file_id = str(uuid.uuid4())
    ext = Path(photo.filename).suffix.lower() or ".jpg"
    dest_filename = f"{file_id}{ext}"
    dest_path = UPLOAD_DIR / dest_filename

    try:
        content = await photo.read()
        if len(content) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty or too small to be a valid crop photo."
            )
        with open(dest_path, "wb") as f:
            f.write(content)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to write uploaded photo: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not process uploaded image file: {str(e)}"
        )

    # Validate image data integrity using service
    try:
        diag_res = pest_detection_service.analyze_photo(
            image_path=str(dest_path),
            filename=photo.filename,
            suspected_pest=suspected_pest,
            crop_hint=crop_hint
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        logger.error(f"Diagnosis processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image diagnosis encountered an unexpected error: {str(e)}"
        )

    # Calculate severity & plot area for DGCA Drone Spray SOP
    area_acres = 1.0
    valid_plot_uuid = None
    if plot_id:
        try:
            valid_plot_uuid = uuid.UUID(str(plot_id))
            try:
                plot_res = await db.execute(select(Plot).where(Plot.id == valid_plot_uuid))
                p = plot_res.scalars().first()
                if p and p.area_acres:
                    area_acres = float(p.area_acres)
            except Exception:
                await db.rollback()
        except Exception:
            valid_plot_uuid = None

    severity = severity_observed_pct if severity_observed_pct is not None else diag_res["estimated_severity_pct"]
    
    # 2. DGCA Drone Spray Prescription generation
    chem_list = diag_res["countermeasures"].get("chemical_countermeasures", [])
    primary_chem = chem_list[0] if chem_list else "Neem Seed Kernel Extract 5%"
    
    # Extract first chemical active ingredient
    active_ing = primary_chem.split("@")[0].split("(")[0].strip()
    
    drone_water_litres = round(DGCA_DRONE_SPRAY_SOP["water_volume_litres_per_acre"] * area_acres, 1)
    drone_prescription = {
        "applicable": bool(drone_spray_requested),
        "target_chemical": active_ing,
        "full_chemical_recommendation": primary_chem,
        "drone_water_volume_litres": drone_water_litres,
        "water_volume_per_acre": f"{DGCA_DRONE_SPRAY_SOP['water_volume_litres_per_acre']} L/acre (ULV)",
        "chemical_rate_per_acre": "Per ICAR package of practices",
        "flight_parameters": {
            "flight_altitude_meters_above_crop": DGCA_DRONE_SPRAY_SOP["flight_altitude_meters_above_canopy"],
            "flight_speed_m_per_s": DGCA_DRONE_SPRAY_SOP["flight_speed_m_per_s"],
            "swath_width_meters": DGCA_DRONE_SPRAY_SOP["swath_width_meters"],
            "nozzle_specification": "Anti-drift Centrifugal / Flat Fan (150-250µm)"
        },
        "flight_safety_limits": DGCA_DRONE_SPRAY_SOP["weather_constraints"]
    }

    photo_url = f"/static/uploads/pest/{dest_filename}"
    
    # 3. Persist to pest_diagnoses table & in-memory store
    diag_id = uuid.uuid4()
    diag_record = PestDiagnosis(
        id=diag_id,
        plot_id=valid_plot_uuid,
        photo_url=photo_url,
        detected_class=diag_res["detected_class"],
        confidence=diag_res["confidence"],
        is_uncertain=diag_res["is_uncertain"],
        alternate_matches=diag_res["alternate_matches"],
        countermeasures=diag_res["countermeasures"],
        drone_prescription=drone_prescription,
        created_at=datetime.now(timezone.utc)
    )

    # In-memory store persistence
    PEST_DIAGNOSES_STORE[str(diag_id)] = {
        "id": str(diag_id),
        "plot_id": str(valid_plot_uuid) if valid_plot_uuid else None,
        "photo_url": photo_url,
        "detected_class": diag_res["detected_class"],
        "confidence": diag_res["confidence"],
        "confidence_pct": diag_res["confidence_pct"],
        "is_uncertain": diag_res["is_uncertain"],
        "alternate_matches": diag_res["alternate_matches"],
        "countermeasures": diag_res["countermeasures"],
        "drone_prescription": drone_prescription,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    # Database persistence with resilient rollback
    try:
        db.add(diag_record)
        await db.commit()
        await db.refresh(diag_record)
    except Exception as dbe:
        logger.warning(f"Database write skipped or rolled back (in-memory store active): {dbe}")
        try:
            await db.rollback()
        except Exception:
            pass

    return {
        "id": str(diag_id),
        "photo_url": photo_url,
        "detected_class": diag_res["detected_class"],
        "scientific_name": diag_res["scientific_name"],
        "confidence": diag_res["confidence"],
        "confidence_pct": diag_res["confidence_pct"],
        "is_uncertain": diag_res["is_uncertain"],
        "uncertainty_message": diag_res["uncertainty_message"],
        "alternate_matches": diag_res["alternate_matches"],
        "countermeasures": diag_res["countermeasures"],
        "is_general_advice": diag_res["is_general_advice"],
        "regulatory_note": diag_res["regulatory_note"],
        "estimated_severity_pct": severity,
        "drone_prescription": drone_prescription,
        "detection_source": diag_res["detection_source"]
    }


@router.post("/confirm-selection", summary="Confirm or manual select pest from candidate cards")
async def confirm_pest_selection(payload: ManualPestSelectPayload, db: AsyncSession = Depends(get_db)):
    """
    Used when a farmer selects a specific candidate card (especially during low-confidence diagnosis)
    or manually selects one of the 8 target pests.
    """
    ref = find_pest_reference(payload.pest_name, crop_hint=payload.crop_hint)
    if not ref:
        ref = GENERIC_COUNTERMEASURES

    # Prepare DGCA drone prescription
    chem_list = ref.get("chemical_countermeasures", [])
    primary_chem = chem_list[0] if chem_list else "Neem Seed Kernel Extract 5%"
    active_ing = primary_chem.split("@")[0].split("(")[0].strip()

    drone_prescription = {
        "applicable": bool(payload.drone_spray_requested),
        "target_chemical": active_ing,
        "full_chemical_recommendation": primary_chem,
        "drone_water_volume_litres": 10.0,
        "water_volume_per_acre": "10 L/acre (ULV)",
        "chemical_rate_per_acre": "Per ICAR package of practices",
        "flight_parameters": {
            "flight_altitude_meters_above_crop": DGCA_DRONE_SPRAY_SOP["flight_altitude_meters_above_canopy"],
            "flight_speed_m_per_s": DGCA_DRONE_SPRAY_SOP["flight_speed_m_per_s"],
            "swath_width_meters": DGCA_DRONE_SPRAY_SOP["swath_width_meters"],
            "nozzle_specification": "Anti-drift Centrifugal / Flat Fan (150-250µm)"
        },
        "flight_safety_limits": DGCA_DRONE_SPRAY_SOP["weather_constraints"]
    }

    return {
        "pest_name": ref["pest_name"],
        "scientific_name": ref["scientific_name"],
        "affected_crops": ref.get("affected_crops", []),
        "symptoms": ref.get("symptoms", ""),
        "countermeasures": ref,
        "regulatory_note": ref.get("regulatory_note"),
        "severity_observed_pct": payload.severity_observed_pct,
        "drone_prescription": drone_prescription
    }


@router.get("/reference", summary="List official ICAR pest & disease reference dataset")
async def get_all_pest_references():
    """Returns the exact 8-entry ICAR reference dataset."""
    return PEST_REFERENCE_DATA


@router.get("/history/{plot_id}", summary="Get past pest diagnoses for a plot")
async def get_pest_diagnosis_history(plot_id: str, db: AsyncSession = Depends(get_db)):
    """Returns list of past diagnoses from in-memory store or database."""
    history = [v for v in PEST_DIAGNOSES_STORE.values() if v.get("plot_id") == plot_id]
    if not history:
        # Check all if plot_id is default
        history = list(PEST_DIAGNOSES_STORE.values())
    return history
