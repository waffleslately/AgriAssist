import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from app.db.base import Base

class Plot(Base):
    __tablename__ = "plots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), default="My Farm", nullable=False)
    
    # PostGIS spatial geometries (WGS84 EPSG:4326)
    boundary = mapped_column(Geometry("POLYGON", srid=4326), nullable=False)
    centroid = mapped_column(Geometry("POINT", srid=4326), nullable=False)

    area_acres: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    soil_texture: Mapped[str] = mapped_column(String(50), nullable=True)  # clay_loam, black_cotton, sandy, etc.
    irrigation_source: Mapped[str] = mapped_column(String(50), nullable=True)  # borewell, canal, rainfed, drip
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    farmer = relationship("Farmer", back_populates="plots")
    crop_cycles = relationship("CropCycle", back_populates="plot", cascade="all, delete-orphan")
    satellite_observations = relationship("SatelliteObservation", back_populates="plot", cascade="all, delete-orphan")
