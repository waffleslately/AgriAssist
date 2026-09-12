from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.soil_service import soil_service
from app.seeds.district_soil_baselines import DISTRICT_SOIL_BASELINES

router = APIRouter()

@router.get("/lookup", summary="Spatial Soil Health lookup by coordinates")
async def lookup_soil(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    state: Optional[str] = Query(None, description="State fallback"),
    district: Optional[str] = Query(None, description="District fallback"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    return await soil_service.get_nearest_soil_sample(
        db=db,
        lat=lat,
        lng=lng,
        state=state,
        district=district
    )

@router.get("/benchmarks", summary="Get pre-calibrated ICAR district soil baselines")
async def get_benchmarks():
    return DISTRICT_SOIL_BASELINES
