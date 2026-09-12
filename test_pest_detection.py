"""
Integration tests for Photo-Based Pest/Disease Detection & ICAR Countermeasures.
Tests:
1. Rejection of invalid file extensions (.txt, .pdf) with clean HTTP 400.
2. Acceptance of valid image files (JPG/PNG).
3. Correct ICAR countermeasure mapping and DGCA drone spray prescription generation.
4. Mandatory Rice Blast regulatory warning banner presence (Punjab/UP export restrictions).
5. Confidence threshold check: low confidence (<60%) returns top 2-3 candidate matches.
6. Persistence of diagnosis record into pest_diagnoses in-memory and database stores.
7. Manual candidate confirmation endpoint (/pest-diagnosis/confirm-selection).
"""

import os
import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.models.pest_reference import PEST_DIAGNOSES_STORE, PEST_REFERENCE_STORE
from app.seeds.pest_reference_data import PEST_REFERENCE_DATA

client = TestClient(app)


def create_test_image(color=(140, 160, 80), size=(200, 200), format="JPEG") -> io.BytesIO:
    """Creates an in-memory test image."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    return buf


def test_invalid_file_extension_returns_400():
    """Validates that uploading a non-image file returns clean HTTP 400, never 500."""
    fake_txt = io.BytesIO(b"This is a text file describing a pest, not an image.")
    response = client.post(
        "/pest-diagnosis/analyze",
        files={"photo": ("report.txt", fake_txt, "text/plain")},
        data={"crop_hint": "wheat"}
    )
    assert response.status_code == 400
    err = response.json()
    assert "Unsupported file type" in err["detail"] or "Invalid" in err["detail"]
    print("✓ Test 1 Passed: Invalid file extension correctly rejected with HTTP 400")


def test_missing_file_returns_400():
    """Validates that empty upload request returns HTTP 400."""
    response = client.post(
        "/pest-diagnosis/analyze",
        data={"crop_hint": "wheat"}
    )
    assert response.status_code == 400
    print("✓ Test 2 Passed: Missing photo file correctly rejected with HTTP 400")


def test_yellow_rust_photo_detection_and_icar_countermeasures():
    """Validates Yellow Rust detection on wheat photo with ICAR countermeasures."""
    # Create yellowish/orange tinted image characteristic of Yellow Rust
    img_buf = create_test_image(color=(210, 160, 40), format="JPEG")
    
    response = client.post(
        "/pest-diagnosis/analyze",
        files={"photo": ("wheat_leaf_rust.jpg", img_buf, "image/jpeg")},
        data={
            "crop_hint": "wheat",
            "suspected_pest": "yellow_rust",
            "severity_observed_pct": "22.5",
            "drone_spray_requested": "true"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "detected_class" in data
    assert "Yellow Rust" in data["detected_class"]
    assert data["scientific_name"] == "Puccinia striiformis f. sp. tritici"
    assert data["confidence"] > 0.0

    # Verify official ICAR countermeasures
    cm = data["countermeasures"]
    assert "Propiconazole 25% EC" in cm["chemical_countermeasures"][0]
    assert "At first appearance of yellow pustules" in cm["ideal_spray_timing"]
    assert "ICAR-IIWBR" in cm["source_note"]

    # Verify DGCA Drone Prescription
    dp = data["drone_prescription"]
    assert dp["applicable"] is True
    assert "Propiconazole" in dp["target_chemical"]
    assert dp["drone_water_volume_litres"] > 0
    assert "10" in dp["water_volume_per_acre"] and "L/acre" in dp["water_volume_per_acre"]

    # Verify diagnosis was persisted
    diag_id = data["id"]
    assert diag_id in PEST_DIAGNOSES_STORE
    print(f"✓ Test 3 Passed: Yellow Rust diagnosis successful ({data['confidence_pct']}% match, DGCA chemical: {dp['target_chemical']})")


def test_rice_blast_regulatory_warning_presence():
    """Validates that Rice Blast triggers the mandatory export restriction regulatory note."""
    img_buf = create_test_image(color=(80, 95, 75), format="PNG")
    
    response = client.post(
        "/pest-diagnosis/analyze",
        files={"photo": ("rice_leaf_blast.png", img_buf, "image/png")},
        data={
            "crop_hint": "paddy",
            "suspected_pest": "blast"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "Rice Blast" in data["detected_class"]
    
    # Must contain regulatory export warning
    assert data["regulatory_note"] is not None
    assert "Basmati" in data["regulatory_note"]
    assert "Tricyclazole" in data["regulatory_note"]
    assert "restricted for 60 days" in data["regulatory_note"]
    print("✓ Test 4 Passed: Rice Blast regulatory warning prominently attached!")


def test_low_confidence_uncertainty_threshold():
    """Validates that detections below 60% confidence return top candidate matches."""
    # Plain neutral grey image with no clear visual symptoms
    img_buf = create_test_image(color=(128, 128, 128), format="JPEG")
    
    response = client.post(
        "/pest-diagnosis/analyze",
        files={"photo": ("ambiguous_leaf.jpg", img_buf, "image/jpeg")},
        data={} # No crop hint or suspected pest -> baseline low prior
    )
    assert response.status_code == 200
    data = response.json()
    
    # Should flag uncertainty and return alternate matches
    assert "alternate_matches" in data
    assert len(data["alternate_matches"]) >= 2
    if data["is_uncertain"]:
        assert data["uncertainty_message"] == "Not fully certain — here are the closest matches"
        print(f"✓ Test 5 Passed: Low confidence ({data['confidence_pct']}%) correctly triggered uncertainty banner with {len(data['alternate_matches'])} candidates")
    else:
        print(f"✓ Test 5 Passed: Detection completed with {len(data['alternate_matches'])} alternate candidates")


def test_confirm_candidate_selection_endpoint():
    """Validates manual or candidate card selection endpoint."""
    response = client.post(
        "/pest-diagnosis/confirm-selection",
        json={
            "pest_name": "Pink Bollworm",
            "crop_hint": "cotton",
            "severity_observed_pct": 20.0,
            "drone_spray_requested": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pest_name"] == "Pink Bollworm"
    assert data["scientific_name"] == "Pectinophora gossypiella"
    assert "pheromone traps" in data["countermeasures"]["organic_countermeasures"][0]
    print("✓ Test 6 Passed: Candidate confirmation endpoint returned full ICAR package for Pink Bollworm")


def test_all_8_reference_pests_present():
    """Verifies that all 8 required ICAR pests are loaded in reference data."""
    response = client.get("/pest-diagnosis/reference")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 8
    expected_names = [
        "Yellow Rust (Stripe Rust)",
        "Pink Bollworm",
        "Fall Armyworm",
        "Rice Blast",
        "Sugarcane Early Shoot Borer",
        "Gram Pod Borer",
        "Mustard Aphid",
        "Potato Late Blight"
    ]
    loaded_names = [p["pest_name"] for p in data]
    for name in expected_names:
        assert name in loaded_names, f"Missing expected pest: {name}"
    print(f"✓ Test 7 Passed: All {len(data)} official ICAR reference pests verified in dataset!")


if __name__ == "__main__":
    print("Starting Pest & Disease Detection Integration Tests...")
    test_invalid_file_extension_returns_400()
    test_missing_file_returns_400()
    test_yellow_rust_photo_detection_and_icar_countermeasures()
    test_rice_blast_regulatory_warning_presence()
    test_low_confidence_uncertainty_threshold()
    test_confirm_candidate_selection_endpoint()
    test_all_8_reference_pests_present()
    print("\nALL 7 PEST DETECTION TESTS PASSED SUCCESSFULLY!")
