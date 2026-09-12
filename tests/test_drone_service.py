import pytest
from app.services.drone_service import drone_service

def test_drone_patch_detection_and_zoning():
    coords = [
        [75.8500, 30.9000],
        [75.8550, 30.9000],
        [75.8550, 30.9050],
        [75.8500, 30.9050],
        [75.8500, 30.9000]
    ]
    analysis = drone_service.analyze_drone_orthomosaic_patches(
        plot_coordinates=coords,
        total_plot_area_acres=10.0,
        sensor_type="Multispectral"
    )

    assert analysis["total_patches_identified"] > 0
    assert analysis["sensor_type"] == "Multispectral"
    assert "Variable Rate Spraying" in analysis["management_recommendations"][0]

    patches = analysis["patches"]
    patch_types = [p["patch_type"] for p in patches]
    assert "healthy_stand" in patch_types
    assert "stressed_crop" in patch_types
    assert "bare_soil_gap" in patch_types

    # Ensure sum of percentages equals approximately 100%
    total_pct = sum(p["percentage_of_plot"] for p in patches)
    assert 95.0 <= total_pct <= 105.0

    # Verify GeoJSON polygon format
    first_patch = patches[0]
    assert first_patch["geojson_geometry"]["type"] == "Polygon"
    assert len(first_patch["geojson_geometry"]["coordinates"][0]) >= 4
