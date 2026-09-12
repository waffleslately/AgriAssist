import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field

class PestDiagnoseRequest(BaseModel):
    plot_id: uuid.UUID
    crop_cycle_id: uuid.UUID
    drone_survey_id: Optional[uuid.UUID] = None
    crop_name: str = Field(..., description="cotton, maize, paddy, wheat, soybean")
    pest_key: str = Field(..., description="e.g. pink_bollworm, fall_armyworm, yellow_rust, yellow_stem_borer, blast, whitefly")
    severity_observed_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of plants/canopy affected")
    drone_spray_requested: bool = Field(default=True, description="Generate DGCA-compliant drone spraying prescription")

class PestReportResponse(BaseModel):
    id: Optional[uuid.UUID] = None
    crop: str
    pest_name: str
    scientific_name: Optional[str]
    severity_observed_pct: float
    economic_threshold_breached: bool
    etl_guideline: str
    ipm_measures: Dict[str, Any]
    drone_spray_prescription: Dict[str, Any]
    localized_advice: Dict[str, str]

    model_config = ConfigDict(from_attributes=True)
