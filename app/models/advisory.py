import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Advisory(Base):
    __tablename__ = "advisories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False)
    trigger_source: Mapped[str] = mapped_column(String(50), nullable=False)  # onboarding, periodic, weather_alert
    crop_stage: Mapped[str] = mapped_column(String(50), nullable=True)  # vegetative, tillering, flowering, etc.
    fertilizer_plan: Mapped[dict] = mapped_column(JSON, nullable=False)
    irrigation_advice: Mapped[str] = mapped_column(Text, nullable=True)
    weather_summary: Mapped[dict] = mapped_column(JSON, nullable=True)
    localized_message: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"en": "...", "hi": "..."}
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    crop_cycle = relationship("CropCycle", back_populates="advisories")
