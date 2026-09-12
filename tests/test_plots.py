import pytest
from app.schemas.plot import GeoJSONPolygon
from app.api.v1.endpoints.plots import calculate_geodesic_area_acres

def test_valid_geojson_polygon():
    coords = [
        [
            [75.8500, 30.9000],
            [75.8550, 30.9000],
            [75.8550, 30.9050],
            [75.8500, 30.9050],
            [75.8500, 30.9000]
        ]
    ]
    poly = GeoJSONPolygon(type="Polygon", coordinates=coords)
    assert poly.type == "Polygon"
    assert len(poly.coordinates[0]) == 5

def test_auto_close_polygon_ring():
    # Only 4 points without closing point
    coords = [
        [
            [75.8500, 30.9000],
            [75.8550, 30.9000],
            [75.8550, 30.9050],
            [75.8500, 30.9050]
        ]
    ]
    poly = GeoJSONPolygon(type="Polygon", coordinates=coords)
    # Validator auto-closes ring
    assert poly.coordinates[0][0] == poly.coordinates[0][-1]

def test_geodesic_area_calculation():
    # A box approximately ~500m x ~500m (~60 acres)
    coords = [
        [75.8500, 30.9000],
        [75.8550, 30.9000],
        [75.8550, 30.9050],
        [75.8500, 30.9050],
        [75.8500, 30.9000]
    ]
    acres = calculate_geodesic_area_acres(coords)
    assert acres > 0.0
    assert 40.0 <= acres <= 80.0
