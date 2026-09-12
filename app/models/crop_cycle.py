import uuid
from datetime import date, datetime, timezone
from sqlalchemy import String, Numeric, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class CropCycle(Base):
    __tablename__ = "crop_cycles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    plot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plots.id", ondelete="CASCADE"), nullable=False)
    crop_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # paddy, wheat, cotton, etc.
    variety: Mapped[str] = mapped_column(String(100), nullable=True)
    season: Mapped[str] = mapped_column(String(20), nullable=False)  # kharif, rabi, zaid
    sowing_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_harvest_date: Mapped[date] = mapped_column(Date, nullable=True)
    target_yield_quintal_per_acre: Mapped[float] = mapped_column(Numeric(6, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    plot = relationship("Plot", back_populates="crop_cycles")
    advisories = relationship("Advisory", back_populates="crop_cycle", cascade="all, delete-orphan")
