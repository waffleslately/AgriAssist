import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy import String, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class UserSoilReport(Base):
    __tablename__ = "user_soil_reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[str] = mapped_column(String(100), index=True, nullable=True)
    plot_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    
    raw_file_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_format: Mapped[str] = mapped_column(String(50), default="pdf")  # pdf, image, csv, manual
    
    # Standard extracted schema (NPK, pH, OC, EC, micronutrients, confidence, needs_manual_review)
    extracted_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    reviewed_and_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

# Resilient in-memory store for local/offline dev environments
USER_SOIL_REPORTS_STORE: Dict[str, Dict[str, Any]] = {}
