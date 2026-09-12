import uuid
from datetime import datetime, date
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator
from shapely.geometry import Polygon, shape

class GeoJSONPolygon(BaseModel):
    type: str = "Polygon"
    coordinates: List[List[List[float]]] = Field(
        ...,
        description="GeoJSON Polygon coordinates: [[[lng, lat], [lng, lat], ...]] (ring must be closed)"
    )

    @field_validator("coordinates")
    @classmethod
    def validate_polygon_geometry(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Polygon must have at least one linear ring.")
        outer_ring = v[0]
        if len(outer_ring) < 4:
            raise ValueError("Outer linear ring must contain at least 4 coordinate positions (first and last identical).")
        # Check closed ring
        if outer_ring[0] != outer_ring[-1]:
            # Auto-close ring for convenience
            outer_ring.append(outer_ring[0])
        # Validate coordinate ranges (lng, lat)
        for pt in outer_ring:
            if len(pt) < 2:
                raise ValueError(f"Invalid coordinate point: {pt}")
            lng, lat = pt[0], pt[1]
            if not (-180.0 <= lng <= 180.0):
                raise ValueError(f"Longitude {lng} out of range [-180, 180]")
            if not (-90.0 <= lat <= 90.0):
                raise ValueError(f"Latitude {lat} out of range [-90, 90]")
        return v

class PlotBase(BaseModel):
    name: str = Field(default="My Farm")
    soil_texture: Optional[str] = Field(default=None, description="clay_loam, sandy, black_cotton, alluvial")
    irrigation_source: Optional[str] = Field(default="borewell", description="borewell, canal, rainfed, drip")

class PlotCreate(PlotBase):
    farmer_id: uuid.UUID
    boundary: GeoJSONPolygon

class PlotResponse(PlotBase):
    id: uuid.UUID
    farmer_id: uuid.UUID
    area_acres: float
    centroid_lat: float
    centroid_lng: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Schema for the comprehensive vertical slice onboarding endpoint
class PlotOnboardRequest(BaseModel):
    phone_number: str = Field(..., description="Farmer phone number")
    farmer_name: Optional[str] = "Kisan"
    state: str = Field(..., description="Indian State")
    district: str = Field(..., description="District")
    sub_district: Optional[str] = None
    village: Optional[str] = None
    language: str = Field(default="hi", description="hi, en, mr, te")
    plot_name: str = Field(default="Main Plot")
    boundary: GeoJSONPolygon
    soil_texture: Optional[str] = None
    irrigation_source: Optional[str] = "borewell"
    # Initial Crop Details
    crop_name: str = Field(..., description="paddy, wheat, cotton, soybean, maize")
    variety: Optional[str] = None
    season: str = Field(default="kharif", description="kharif, rabi, zaid")
    sowing_date: date = Field(..., description="Date crop was sown (YYYY-MM-DD)")
    target_yield_quintal_per_acre: Optional[float] = None
