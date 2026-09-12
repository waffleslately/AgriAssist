import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Numeric, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry
from app.db.base import Base

class PestDetectionReport(Base):
    __tablename__ = "pest_detection_reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    plot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plots.id", ondelete="CASCADE"), nullable=False)
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False)
    drone_survey_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drone_surveys.id", ondelete="SET NULL"), nullable=True)

    detection_source: Mapped[str] = mapped_column(String(50), default="drone_spectral")  # drone_spectral, farmer_photo_cv, field_scouting
    pest_or_disease_name: Mapped[str] = mapped_column(String(100), nullable=False)
    scientific_name: Mapped[str] = mapped_column(String(100), nullable=True)
    severity_score: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)  # 0.00 to 1.00
    
    # Economic Threshold Level (ETL) check
    economic_threshold_breached: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Infested boundary if detected by drone
    affected_patch_geometry = mapped_column(Geometry("POLYGON", srid=4326), nullable=True)

    # Integrated Pest Management & Drone Spray Specifications
    prescribed_ipm_measures: Mapped[dict] = mapped_column(JSON, nullable=False)
    drone_spray_prescription: Mapped[dict] = mapped_column(JSON, nullable=True)
    localized_advice: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"en": "...", "hi": "..."}

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
