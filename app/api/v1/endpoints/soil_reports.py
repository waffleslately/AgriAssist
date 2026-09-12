import uuid
import logging
from datetime import datetime, timezone, date
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.soil_report import UserSoilReport, USER_SOIL_REPORTS_STORE
from app.services.soil_report_parser import soil_report_parser
from app.services.crop_recommender import crop_recommender
from app.services.agronomy_engine import agronomy_engine
from app.services.soil_service import soil_service
from app.services.weather_service import weather_service
from app.services.localization_service import LocalizationService

logger = logging.getLogger("agri_backend.soil_reports")

router = APIRouter()

class SoilReportTextPayload(BaseModel):
    text: str
    farmer_id: Optional[str] = "default_farmer"
    plot_id: Optional[str] = None

class SoilConfirmPayload(BaseModel):
    nitrogen_kg_ha: Optional[float] = None
    phosphorus_kg_ha: Optional[float] = None
    potassium_kg_ha: Optional[float] = None
    ph: Optional[float] = None
    organic_carbon_pct: Optional[float] = None
    electrical_conductivity: Optional[float] = None
    state: Optional[str] = "Punjab"
    district: Optional[str] = "Ludhiana"
    latitude: Optional[float] = 30.90
    longitude: Optional[float] = 75.85

class NutrientPlanPayload(BaseModel):
    crop: str
    variety: Optional[str] = None
    area_acres: Optional[float] = 1.0
    sowing_date: Optional[str] = None

@router.post("/upload")
async def upload_soil_report(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    farmer_id: Optional[str] = Form("default_farmer"),
    plot_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts Soil Health Card / soil report in ANY format:
    PDF (text or scanned), Image (JPG/PNG), CSV/Excel, or plain text.
    Extracts N, P, K, pH, OC, EC and returns standard schema with confidence metrics.
    """
    report_id = uuid.uuid4()
    source_format = "manual"
    raw_url = None

    if file:
        file_bytes = await file.read()
        filename = file.filename or "report.txt"
        extracted = soil_report_parser.parse_file(file_bytes, filename)
        source_format = extracted.get("source_format", "file")
        raw_url = f"/static/uploads/soil_reports/{report_id}_{filename}"
    elif raw_text:
        extracted = soil_report_parser.extract_from_text(raw_text, source_format="manual")
    else:
        raise HTTPException(status_code=400, detail="Either a report file or raw text input is required.")

    # In-memory storage for immediate local resilience
    report_record = {
        "id": str(report_id),
        "farmer_id": farmer_id,
        "plot_id": plot_id,
        "raw_file_url": raw_url,
        "source_format": source_format,
        "extracted_data": extracted,
        "reviewed_and_confirmed": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    USER_SOIL_REPORTS_STORE[str(report_id)] = report_record

    # Optional DB write if PostgreSQL is running
    try:
        db_report = UserSoilReport(
            id=report_id,
            farmer_id=farmer_id,
            plot_id=uuid.UUID(plot_id) if plot_id else None,
            raw_file_url=raw_url,
            source_format=source_format,
            extracted_data=extracted,
            reviewed_and_confirmed=False
        )
        db.add(db_report)
        await db.commit()
    except Exception as e:
        logger.warning(f"Database write skipped (running in-memory mode): {e}")
        try:
            await db.rollback()
        except Exception:
            pass

    return {
        "report_id": str(report_id),
        "status": "extracted",
        "extracted_data": extracted
    }

@router.post("/{report_id}/confirm")
async def confirm_soil_report(
    report_id: str,
    payload: SoilConfirmPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    Farmer confirms/edits extracted values.
    Applies Section 4 Area-based / Geographic fallback via SoilService for any missing values.
    """
    report = USER_SOIL_REPORTS_STORE.get(report_id)
    if not report:
        # Create virtual report if confirmed directly from UI
        report = {
            "id": report_id,
            "farmer_id": "current_farmer",
            "extracted_data": {},
            "reviewed_and_confirmed": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        USER_SOIL_REPORTS_STORE[report_id] = report

    confirmed_data = dict(report.get("extracted_data", {}))

    # Fill from payload
    if payload.nitrogen_kg_ha is not None:
        confirmed_data["nitrogen_kg_ha"] = payload.nitrogen_kg_ha
    if payload.phosphorus_kg_ha is not None:
        confirmed_data["phosphorus_kg_ha"] = payload.phosphorus_kg_ha
    if payload.potassium_kg_ha is not None:
        confirmed_data["potassium_kg_ha"] = payload.potassium_kg_ha
    if payload.ph is not None:
        confirmed_data["ph"] = payload.ph
    if payload.organic_carbon_pct is not None:
        confirmed_data["organic_carbon_pct"] = payload.organic_carbon_pct
    if payload.electrical_conductivity is not None:
        confirmed_data["electrical_conductivity"] = payload.electrical_conductivity

    # Check for missing values and apply Section 4 Geographic Fallback
    missing_fields = [k for k in ["nitrogen_kg_ha", "phosphorus_kg_ha", "potassium_kg_ha", "ph"] if confirmed_data.get(k) is None]
    if missing_fields:
        logger.info(f"Applying SoilService ICAR baseline fallback for missing fields: {missing_fields}")
        baseline = await soil_service.get_nearest_soil_sample(
            db=db,
            lat=payload.latitude or 30.90,
            lng=payload.longitude or 75.85,
            state=payload.state,
            district=payload.district
        )
        if confirmed_data.get("nitrogen_kg_ha") is None:
            confirmed_data["nitrogen_kg_ha"] = baseline.get("available_nitrogen_kg_ha", 250.0)
            confirmed_data["nitrogen_is_fallback"] = True
        if confirmed_data.get("phosphorus_kg_ha") is None:
            confirmed_data["phosphorus_kg_ha"] = baseline.get("available_phosphorus_kg_ha", 18.0)
            confirmed_data["phosphorus_is_fallback"] = True
        if confirmed_data.get("potassium_kg_ha") is None:
            confirmed_data["potassium_kg_ha"] = baseline.get("available_potassium_kg_ha", 280.0)
            confirmed_data["potassium_is_fallback"] = True
        if confirmed_data.get("ph") is None:
            confirmed_data["ph"] = baseline.get("ph", 7.4)
            confirmed_data["ph_is_fallback"] = True
        if confirmed_data.get("organic_carbon_pct") is None:
            confirmed_data["organic_carbon_pct"] = baseline.get("organic_carbon_pct", 0.5)

    report["extracted_data"] = confirmed_data
    report["reviewed_and_confirmed"] = True

    return {
        "report_id": report_id,
        "status": "confirmed",
        "reviewed_and_confirmed": True,
        "soil_metrics": confirmed_data
    }

@router.post("/{report_id}/suggest-crops")
async def suggest_crops_from_soil(
    report_id: str,
    latitude: Optional[float] = 30.90,
    longitude: Optional[float] = 75.85,
    db: AsyncSession = Depends(get_db)
):
    """
    Feature 3A: Suggest suitable crops based on Atharva Ingle's Kaggle Crop Recommendation Dataset.
    Uses confirmed N, P, K, pH and localized WeatherService climate averages.
    """
    report = USER_SOIL_REPORTS_STORE.get(report_id)
    if not report:
        # Fallback to default soil values if testing without prior report
        n = 190.0
        p = 18.0
        k = 130.0
        ph = 7.4
    else:
        ext = report.get("extracted_data", {})
        n = float(ext.get("nitrogen_kg_ha") or 190.0)
        p = float(ext.get("phosphorus_kg_ha") or 18.0)
        k = float(ext.get("potassium_kg_ha") or 130.0)
        ph = float(ext.get("ph") or 7.4)

    # Fetch weather metrics from existing WeatherService
    weather = await weather_service.get_forecast(latitude, longitude)
    avg_temp = (weather.get("max_temp", 31.0) + weather.get("min_temp", 22.0)) / 2.0
    rain_48h = weather.get("precipitation_48h_mm", 0.0)
    # Estimate typical monthly rain (scaled from 48h or regional baseline)
    est_rainfall = max(45.0, rain_48h * 15.0)

    # Rank crops against Kaggle Crop Recommendation distributions
    top_crops = crop_recommender.rank_crops(
        n=n,
        p=p,
        k=k,
        ph=ph,
        temperature=avg_temp,
        humidity=65.0,
        rainfall=est_rainfall,
        top_n=5
    )

    formatted_crops = []
    for idx, c in enumerate(top_crops):
        fit_pct = round(c["fit_score"] * 100, 1) if c["fit_score"] <= 1.0 else round(c["fit_score"], 1)
        formatted_crops.append({
            "rank": idx + 1,
            "crop": c["crop"],
            "crop_id": c["crop"],
            "display_name": c.get("display_name", c["crop"].capitalize()),
            "season": c.get("season", "general"),
            "fit_score": fit_pct,
            "why_suitable": c.get("why", ""),
            "why": c.get("why", ""),
            "ideal_ranges": c.get("ideal_ranges", {})
        })

    return {
        "report_id": report_id,
        "input_soil": {
            "nitrogen_kg_ha": n,
            "phosphorus_kg_ha": p,
            "potassium_kg_ha": k,
            "ph": ph
        },
        "climate_context": {
            "avg_temperature_c": round(avg_temp, 1),
            "estimated_rainfall_mm": round(est_rainfall, 1)
        },
        "suggested_crops": formatted_crops
    }

@router.post("/{report_id}/nutrient-plan")
async def calculate_nutrient_plan_for_crop(
    report_id: str,
    payload: NutrientPlanPayload,
    latitude: Optional[float] = 30.90,
    longitude: Optional[float] = 75.85,
    db: AsyncSession = Depends(get_db)
):
    """
    Feature 3B: Suggest nutrients for a chosen crop.
    Reuses existing AgronomyEngine STCR calibration and fertilizer bag conversion logic.
    Returns plain-language bilingual plan (English + Hindi).
    """
    report = USER_SOIL_REPORTS_STORE.get(report_id)
    if not report:
        n = 190.0
        p = 18.0
        k = 130.0
        ph = 7.4
        oc = 0.45
    else:
        ext = report.get("extracted_data", {})
        n = float(ext.get("nitrogen_kg_ha") or 190.0)
        p = float(ext.get("phosphorus_kg_ha") or 18.0)
        k = float(ext.get("potassium_kg_ha") or 130.0)
        ph = float(ext.get("ph") or 7.4)
        oc = float(ext.get("organic_carbon_pct") or 0.45)

    soil_metrics = {
        "available_nitrogen_kg_ha": n,
        "available_phosphorus_kg_ha": p,
        "available_potassium_kg_ha": k,
        "ph": ph,
        "organic_carbon_pct": oc
    }

    # Fetch weather metrics to enforce rain hold warnings
    weather = await weather_service.get_forecast(latitude, longitude)

    # Use sowing date or today
    sowing_d = date.today()
    if payload.sowing_date:
        try:
            sowing_d = date.fromisoformat(payload.sowing_date)
        except ValueError:
            sowing_d = date.today()

    # Reuse EXISTING AgronomyEngine calculate_plan
    plan = agronomy_engine.calculate_plan(
        crop_name=payload.crop,
        sowing_date=sowing_d,
        soil_metrics=soil_metrics,
        satellite_metrics={"mean_ndvi": 0.60, "soil_moisture_proxy": 0.25},
        weather_metrics=weather,
        area_acres=payload.area_acres or 1.0,
        current_date=sowing_d  # basal calculation
    )

    # Generate localized plain language plan using existing LocalizationService
    localized_advisory = LocalizationService.generate_localized_advisory(plan, language="hi")

    sched = plan.get("fertilizer_schedule", [])
    urea_acre = 0.0
    dap_acre = 0.0
    mop_acre = 0.0
    urea_total = 0.0
    dap_total = 0.0
    mop_total = 0.0
    bag_summaries = []

    for item in sched:
        fert_name = item.get("fertilizer", "").lower()
        bags_ac = float(item.get("bags_per_acre", 0.0))
        bags_tot = float(item.get("total_bags_for_plot", 0.0))
        bag_summaries.append(f"{item['bags_per_acre']} bags of {item['fertilizer']} per acre")
        if "urea" in fert_name:
            urea_acre += bags_ac
            urea_total += bags_tot
        elif "dap" in fert_name:
            dap_acre += bags_ac
            dap_total += bags_tot
        elif "mop" in fert_name or "potash" in fert_name:
            mop_acre += bags_ac
            mop_total += bags_tot

    if bag_summaries:
        checklist_en = f"For your {payload.crop.capitalize()} crop: Apply {', and '.join(bag_summaries)} at sowing time."
        checklist_hi = f"आपकी {plan['crop_name']} फसल के लिए: बुवाई के समय प्रति एकड़ {', '.join(bag_summaries)} डालें।"
    else:
        checklist_en = f"Your soil currently has sufficient fertility for {payload.crop.capitalize()}. No chemical fertilizer is required at basal sowing."
        checklist_hi = f"आपकी {plan['crop_name']} फसल के लिए मिट्टी में पोषक तत्व पर्याप्त हैं। अभी रासायनिक खाद की आवश्यकता नहीं है।"

    fertilizer_plan = {
        "commercial_fertilizers_per_acre": {
            "urea_45kg_bags": round(urea_acre, 2),
            "dap_50kg_bags": round(dap_acre, 2),
            "mop_50kg_bags": round(mop_acre, 2)
        },
        "total_field_bags": {
            "urea_45kg_bags": round(urea_total, 1),
            "dap_50kg_bags": round(dap_total, 1),
            "mop_50kg_bags": round(mop_total, 1)
        }
    }

    hindi_guidance = {
        "hindi_prescription": checklist_hi,
        "advisory_hindi": localized_advisory
    }

    return {
        "report_id": report_id,
        "crop": payload.crop,
        "variety": payload.variety,
        "area_acres": payload.area_acres,
        "soil_status": plan.get("soil_status", {}),
        "fertilizer_schedule": sched,
        "fertilizer_plan": fertilizer_plan,
        "total_field_bags": fertilizer_plan["total_field_bags"],
        "commercial_fertilizers_per_acre": fertilizer_plan["commercial_fertilizers_per_acre"],
        "summary_checklist": {
            "en": checklist_en,
            "hi": checklist_hi
        },
        "hindi_guidance": hindi_guidance,
        "advisory_text": localized_advisory
    }

