import uuid
from datetime import date, datetime, timezone
from sqlalchemy import String, Numeric, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry
from app.db.base import Base

class SoilHealthSample(Base):
    __tablename__ = "soil_health_samples"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # farmer_uploaded, shc_portal_grid, district_benchmark
    
    # Point location in WGS84
    location = mapped_column(Geometry("POINT", srid=4326), nullable=False)

    state: Mapped[str] = mapped_column(String(50), index=True, nullable=True)
    district: Mapped[str] = mapped_column(String(50), index=True, nullable=True)
    
    # Primary Nutrients & Chemical Metrics
    organic_carbon_pct: Mapped[float] = mapped_column(Numeric(4, 2), nullable=True)
    available_nitrogen_kg_ha: Mapped[float] = mapped_column(Numeric(6, 1), nullable=True)
    available_phosphorus_kg_ha: Mapped[float] = mapped_column(Numeric(6, 1), nullable=True)
    available_potassium_kg_ha: Mapped[float] = mapped_column(Numeric(6, 1), nullable=True)
    ph: Mapped[float] = mapped_column(Numeric(4, 2), nullable=True)
    electrical_conductivity: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    zinc_ppm: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    iron_ppm: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    sample_date: Mapped[date] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
