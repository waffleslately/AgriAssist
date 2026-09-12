import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, ConfigDict

class FertilizerDose(BaseModel):
    fertilizer: str  # e.g., 'Urea (46% N)', 'DAP (18% N, 46% P2O5)', 'MOP (60% K2O)'
    quantity_kg_per_acre: float
    bags_per_acre: float  # in standard Indian bags (45kg Urea, 50kg DAP, 50kg MOP)
    timing_stage: str     # Basal (At Sowing), 1st Top Dressing, 2nd Top Dressing
    instructions: str

class AdvisoryPlan(BaseModel):
    crop_stage: str
    days_after_sowing: int
    crop_vigor_status: str
    nitrogen_status: str
    phosphorus_status: str
    potassium_status: str
    weather_hold_warning: bool
    weather_hold_reason: Optional[str] = None
    fertilizer_schedule: List[FertilizerDose]
    irrigation_advice: str

class AdvisoryResponse(BaseModel):
    id: uuid.UUID
    crop_cycle_id: uuid.UUID
    trigger_source: str
    crop_stage: str
    fertilizer_plan: Dict[str, Any]
    irrigation_advice: Optional[str]
    weather_summary: Optional[Dict[str, Any]]
    localized_message: Dict[str, str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
