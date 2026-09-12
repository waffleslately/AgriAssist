import uuid
from datetime import date, datetime, timezone
from sqlalchemy import String, Numeric, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class SatelliteObservation(Base):
    __tablename__ = "satellite_observations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    plot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plots.id", ondelete="CASCADE"), nullable=False)
    satellite_source: Mapped[str] = mapped_column(String(30), default="Sentinel-2", nullable=False)
    acquisition_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Vegetation & Moisture Indices
    mean_ndvi: Mapped[float] = mapped_column(Numeric(5, 3), nullable=False)
    p10_ndvi: Mapped[float] = mapped_column(Numeric(5, 3), nullable=True)
    p90_ndvi: Mapped[float] = mapped_column(Numeric(5, 3), nullable=True)
    soil_moisture_proxy: Mapped[float] = mapped_column(Numeric(5, 3), nullable=True)  # NDMI / NDWI / SAR proxy
    cloud_cover_percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    raw_metrics: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    plot = relationship("Plot", back_populates="satellite_observations")
