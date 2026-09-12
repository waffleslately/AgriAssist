from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.farmer import Farmer
from app.schemas.farmer import FarmerCreate, FarmerResponse

router = APIRouter()

@router.post("/", response_model=FarmerResponse, summary="Register or update farmer profile")
async def create_farmer(farmer_in: FarmerCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Farmer).where(Farmer.phone_number == farmer_in.phone_number)
    )
    existing = result.scalars().first()
    if existing:
        for field, value in farmer_in.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        await db.commit()
        await db.refresh(existing)
        return existing

    farmer = Farmer(**farmer_in.model_dump())
    db.add(farmer)
    await db.commit()
    await db.refresh(farmer)
    return farmer

@router.get("/{phone_number}", response_model=FarmerResponse, summary="Get farmer profile by phone")
async def get_farmer_by_phone(phone_number: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Farmer).where(Farmer.phone_number == phone_number)
    )
    farmer = result.scalars().first()
    if not farmer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer profile not found."
        )
    return farmer
