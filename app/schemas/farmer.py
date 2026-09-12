import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class FarmerBase(BaseModel):
    phone_number: str = Field(..., description="Indian 10-digit mobile number, e.g., '9876543210' or '+919876543210'")
    name: Optional[str] = None
    preferred_language: str = Field(default="hi", description="Language code: hi, en, mr, te, pa, etc.")
    state: str = Field(..., description="State, e.g. 'Punjab', 'Maharashtra', 'Madhya Pradesh'")
    district: str = Field(..., description="District, e.g. 'Ludhiana', 'Nashik'")
    sub_district: Optional[str] = None
    village: Optional[str] = None

class FarmerCreate(FarmerBase):
    pass

class FarmerResponse(FarmerBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
