import pytest
from app.services.pest_control_engine import pest_control_engine

def test_fall_armyworm_maize_drone_prescription():
    result = pest_control_engine.diagnose_and_prescribe(
        crop_name="maize",
        pest_key="fall_armyworm",
        severity_observed_pct=15.0, # Breaches ETL (>8%)
        area_acres=3.0,
        drone_spray_requested=True
    )

    assert result["economic_threshold_breached"] is True
    assert "Fall Armyworm" in result["pest_name"]
    
    # Verify drone spray calculation (10 L/acre * 3 acres = 30.0 L water)
    drone_plan = result["drone_spray_prescription"]
    assert drone_plan["applicable"] is True
    assert drone_plan["drone_water_volume_litres"] == 30.0
    assert "Chlorantraniliprole" in drone_plan["target_chemical"]
    assert drone_plan["flight_parameters"]["flight_altitude_meters_above_crop"] == 1.8

    # Verify bilingual advice
    assert "🚨 BREACHED" in result["localized_advice"]["en"]
    assert "ड्रोन छिड़काव निर्देश" in result["localized_advice"]["hi"]

def test_pink_bollworm_cotton_ipm():
    result = pest_control_engine.diagnose_and_prescribe(
        crop_name="cotton",
        pest_key="pink_bollworm",
        severity_observed_pct=5.0, # Below ETL (<8%)
        area_acres=2.0,
        drone_spray_requested=True
    )

    assert result["economic_threshold_breached"] is False
    assert "Pink Bollworm" in result["pest_name"]
    
    ipm = result["ipm_measures"]
    # Check pheromone traps
    assert any("pheromone" in c.lower() for c in ipm["cultural"])
    # Check biological control
    assert "Neem" in ipm["biological"]["name"] or "Trichogramma" in ipm["biological"]["name"]
    # Check CIBRC chemical
    assert "Emamectin Benzoate" in ipm["chemical"]["active_ingredient"]
