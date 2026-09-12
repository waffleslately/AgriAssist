import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.advisory import Advisory
from app.schemas.advisory import AdvisoryResponse

router = APIRouter()

@router.get("/crop-cycle/{crop_cycle_id}", response_model=List[AdvisoryResponse], summary="Get advisories for a crop cycle")
async def get_advisories(crop_cycle_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Advisory)
        .where(Advisory.crop_cycle_id == crop_cycle_id)
        .order_by(Advisory.created_at.desc())
    )
    return result.scalars().all()
