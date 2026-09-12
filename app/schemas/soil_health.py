import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class SoilHealthBase(BaseModel):
    source: str
    state: Optional[str] = None
    district: Optional[str] = None
    organic_carbon_pct: Optional[float] = None
    available_nitrogen_kg_ha: Optional[float] = None
    available_phosphorus_kg_ha: Optional[float] = None
    available_potassium_kg_ha: Optional[float] = None
    ph: Optional[float] = None
    electrical_conductivity: Optional[float] = None
    zinc_ppm: Optional[float] = None
    iron_ppm: Optional[float] = None
    sample_date: Optional[date] = None

class SoilHealthResponse(SoilHealthBase):
    id: uuid.UUID
    distance_km: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
