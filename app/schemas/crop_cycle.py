import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class CropCycleBase(BaseModel):
    crop_name: str = Field(..., description="Crop name: paddy, wheat, cotton, soybean, maize")
    variety: Optional[str] = None
    season: str = Field(..., description="kharif, rabi, zaid")
    sowing_date: date
    expected_harvest_date: Optional[date] = None
    target_yield_quintal_per_acre: Optional[float] = None
    is_active: bool = True

class CropCycleCreate(CropCycleBase):
    plot_id: uuid.UUID

class CropCycleResponse(CropCycleBase):
    id: uuid.UUID
    plot_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
