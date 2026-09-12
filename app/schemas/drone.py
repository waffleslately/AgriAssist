import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

class DroneSurveyCreate(BaseModel):
    plot_id: uuid.UUID
    drone_operator_name: Optional[str] = "Kisan Drone Services"
    sensor_type: str = Field(default="Multispectral", description="RGB, Multispectral, RedEdge, Thermal")
    flight_altitude_meters: float = Field(default=50.0, description="Altitude in meters")
    ground_sampling_distance_cm: float = Field(default=2.5, description="GSD cm/pixel")
    orthomosaic_url: Optional[str] = None

class PlotPatchResponse(BaseModel):
    patch_id: str
    patch_type: str
    severity_level: str
    mean_vigor_score: float
    area_sq_meters: float
    area_acres: float
    percentage_of_plot: float
    notes: Optional[str]
    geojson_geometry: Dict[str, Any]

class DroneSurveyAnalysisResponse(BaseModel):
    survey_id: uuid.UUID
    plot_id: uuid.UUID
    flight_date: datetime
    sensor_type: str
    total_area_acres: float
    overall_stand_uniformity_pct: float
    stressed_area_pct: float
    management_recommendations: List[str]
    patches: List[PlotPatchResponse]

    model_config = ConfigDict(from_attributes=True)
