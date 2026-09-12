import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.satellite_observation import SatelliteObservation
from app.schemas.satellite import SatelliteObservationResponse

router = APIRouter()

@router.get("/plot/{plot_id}/timeseries", response_model=List[SatelliteObservationResponse], summary="Get NDVI & moisture timeseries for a plot")
async def get_plot_timeseries(plot_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SatelliteObservation)
        .where(SatelliteObservation.plot_id == plot_id)
        .order_by(SatelliteObservation.acquisition_date.asc())
    )
    return result.scalars().all()
