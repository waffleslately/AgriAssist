import pytest
from datetime import date
from app.services.agronomy_engine import agronomy_engine
from app.services.localization_service import localization_service

def test_basal_dose_wheat():
    """Verify basal dose calculation for Wheat (Sowing time, DAS 0)."""
    soil = {
        "available_nitrogen_kg_ha": 250.0, # Low N (<280) -> +25%
        "available_phosphorus_kg_ha": 20.0, # Low P (<23) -> +25%
        "available_potassium_kg_ha": 250.0  # Medium K -> 100%
    }
    sat = {"mean_ndvi": 0.30, "soil_moisture_proxy": 0.22}
    weather = {"precipitation_48h_mm": 0.0, "heavy_rain_warning": False}
    
    plan = agronomy_engine.calculate_plan(
        crop_name="wheat",
        sowing_date=date.today(),
        soil_metrics=soil,
        satellite_metrics=sat,
        weather_metrics=weather,
        area_acres=2.0
    )

    assert plan["crop_stage"] == "Basal (Sowing)"
    assert plan["soil_status"]["nitrogen"] == "Low"
    assert plan["soil_status"]["phosphorus"] == "Low"
    assert plan["soil_status"]["potassium"] == "Medium"
    assert not plan["weather_hold_warning"]

    # Verify fertilizers present: DAP, Urea, MOP
    ferts = [f["fertilizer"] for f in plan["fertilizer_schedule"]]
    assert any("DAP" in f for f in ferts)
    assert any("MOP" in f for f in ferts)

def test_top_dressing_weather_hold():
    """Verify that heavy rain (>15mm) triggers the rain hold-off warning."""
    soil = {
        "available_nitrogen_kg_ha": 350.0, # Medium N
        "available_phosphorus_kg_ha": 30.0, # Medium P
        "available_potassium_kg_ha": 250.0  # Medium K
    }
    sat = {"mean_ndvi": 0.58, "soil_moisture_proxy": 0.35}
    weather = {"precipitation_48h_mm": 28.5, "heavy_rain_warning": True}
    
    # 25 days after sowing (Active Tillering for paddy)
    sowing = date.fromordinal(date.today().toordinal() - 25)

    plan = agronomy_engine.calculate_plan(
        crop_name="paddy",
        sowing_date=sowing,
        soil_metrics=soil,
        satellite_metrics=sat,
        weather_metrics=weather,
        area_acres=1.0
    )

    assert plan["crop_stage"] == "Active Tillering"
    assert plan["weather_hold_warning"] is True
    assert "HOLD APPLICATION" in plan["fertilizer_schedule"][0]["instructions"]
    assert "Skip irrigation" in plan["irrigation_advice"]

def test_stunted_ndvi_triggers_alert():
    """Verify that low NDVI (<0.38) during vegetative stage triggers vigor alert."""
    soil = {
        "available_nitrogen_kg_ha": 300.0,
        "available_phosphorus_kg_ha": 30.0,
        "available_potassium_kg_ha": 250.0
    }
    sat = {"mean_ndvi": 0.28, "soil_moisture_proxy": 0.12} # Very low NDVI
    weather = {"precipitation_48h_mm": 0.0, "heavy_rain_warning": False}
    sowing = date.fromordinal(date.today().toordinal() - 30)

    plan = agronomy_engine.calculate_plan(
        crop_name="wheat",
        sowing_date=sowing,
        soil_metrics=soil,
        satellite_metrics=sat,
        weather_metrics=weather,
        area_acres=1.0
    )

    assert plan["crop_vigor_status"] == "Stunted / Low Vigor"
    assert plan["vigor_alert"] is not None
    assert "Zinc Sulphate" in plan["vigor_alert"] or "19:19:19" in plan["vigor_alert"]

def test_bilingual_localization():
    """Verify English & Hindi messages are correctly formatted."""
    soil = {"available_nitrogen_kg_ha": 300.0, "available_phosphorus_kg_ha": 30.0, "available_potassium_kg_ha": 250.0}
    sat = {"mean_ndvi": 0.60, "soil_moisture_proxy": 0.25}
    weather = {"precipitation_48h_mm": 0.0, "heavy_rain_warning": False}

    plan = agronomy_engine.calculate_plan(
        crop_name="wheat",
        sowing_date=date.today(),
        soil_metrics=soil,
        satellite_metrics=sat,
        weather_metrics=weather,
        area_acres=1.0
    )

    loc = localization_service.generate_localized_advisory(plan)
    assert "Crop Advisory" in loc["en"]
    assert "फसल सलाह" in loc["hi"]
    assert "यूरिया" in loc["hi"] or "डीएपी" in loc["hi"]
