import uuid
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from app.db.base import Base

class Livestock(Base):
    __tablename__ = "livestock"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False)
    plot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plots.id", ondelete="SET NULL"), nullable=True)
    
    tag_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    animal_type: Mapped[str] = mapped_column(String(50), nullable=False, default="cattle") # e.g. cattle, sheep, goat
    collar_battery: Mapped[float] = mapped_column(Float, nullable=True) # Last known battery level %
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    farmer = relationship("Farmer")
    plot = relationship("Plot")
    locations = relationship("LivestockLocation", back_populates="livestock", cascade="all, delete-orphan")


class LivestockLocation(Base):
    __tablename__ = "livestock_locations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    livestock_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("livestock.id", ondelete="CASCADE"), nullable=False, index=True)
    
    geom = mapped_column(Geometry("POINT", srid=4326), nullable=False)
    
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    livestock = relationship("Livestock", back_populates="locations")
