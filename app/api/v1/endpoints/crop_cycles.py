import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.crop_cycle import CropCycle
from app.schemas.crop_cycle import CropCycleCreate, CropCycleResponse

router = APIRouter()

@router.post("/", response_model=CropCycleResponse, summary="Create a new crop cycle for a plot")
async def create_crop_cycle(crop_in: CropCycleCreate, db: AsyncSession = Depends(get_db)):
    cycle = CropCycle(**crop_in.model_dump())
    db.add(cycle)
    await db.commit()
    await db.refresh(cycle)
    return cycle

@router.get("/plot/{plot_id}", response_model=List[CropCycleResponse], summary="List all crop cycles for a plot")
async def get_plot_crop_cycles(plot_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CropCycle).where(CropCycle.plot_id == plot_id).order_by(CropCycle.created_at.desc())
    )
    return result.scalars().all()
