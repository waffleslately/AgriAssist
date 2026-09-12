import uuid
from datetime import date, datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class SatelliteObservationBase(BaseModel):
    satellite_source: str = "Sentinel-2"
    acquisition_date: date
    mean_ndvi: float
    p10_ndvi: Optional[float] = None
    p90_ndvi: Optional[float] = None
    soil_moisture_proxy: Optional[float] = None
    cloud_cover_percentage: float = 0.0
    raw_metrics: Optional[Dict[str, Any]] = None

class SatelliteObservationResponse(SatelliteObservationBase):
    id: uuid.UUID
    plot_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
