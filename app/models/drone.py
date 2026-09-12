import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from app.db.base import Base

class DroneSurvey(Base):
    __tablename__ = "drone_surveys"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    plot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plots.id", ondelete="CASCADE"), nullable=False)
    flight_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    drone_operator_name: Mapped[str] = mapped_column(String(100), nullable=True)
    sensor_type: Mapped[str] = mapped_column(String(50), default="Multispectral")  # RGB, Multispectral, RedEdge, Thermal
    flight_altitude_meters: Mapped[float] = mapped_column(Numeric(5, 1), default=50.0)
    ground_sampling_distance_cm: Mapped[float] = mapped_column(Numeric(4, 2), default=2.5)  # e.g., 2.5 cm/pixel
    orthomosaic_url: Mapped[str] = mapped_column(String(255), nullable=True)
    total_area_surveyed_acres: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    patches = relationship("PlotPatch", back_populates="drone_survey", cascade="all, delete-orphan")

class PlotPatch(Base):
    __tablename__ = "plot_patches"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    drone_survey_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drone_surveys.id", ondelete="CASCADE"), nullable=False)
    
    # Patch category: stressed_crop, bare_soil_gap, weed_infestation, waterlogging, healthy_stand
    patch_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity_level: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high, critical
    
    # PostGIS Polygon geometry for spatial hotspot / variable-rate spraying boundary
    patch_geometry = mapped_column(Geometry("POLYGON", srid=4326), nullable=False)

    area_sq_meters: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    percentage_of_plot: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    mean_vigor_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=True)  # 0.000 to 1.000
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    drone_survey = relationship("DroneSurvey", back_populates="patches")


class DroneScan(Base):
    __tablename__ = "drone_scans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    plot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plots.id", ondelete="CASCADE"), nullable=False, index=True)
    scan_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    result_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    plot = relationship("Plot")
