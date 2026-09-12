import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import String, DateTime, JSON, Text, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class PestReference(Base):
    __tablename__ = "pest_reference"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    pest_name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    scientific_name: Mapped[str] = mapped_column(String(100), nullable=False)
    affected_crops: Mapped[List[str]] = mapped_column(JSON, default=list)  # ["wheat", "paddy"]
    symptoms: Mapped[str] = mapped_column(Text, nullable=False)
    organic_countermeasures: Mapped[List[str]] = mapped_column(JSON, default=list)
    chemical_countermeasures: Mapped[List[str]] = mapped_column(JSON, default=list)
    ideal_spray_timing: Mapped[str] = mapped_column(Text, nullable=False)
    regulatory_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class PestDiagnosis(Base):
    __tablename__ = "pest_diagnoses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    plot_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True, index=True)
    photo_url: Mapped[str] = mapped_column(String(255), nullable=False)
    detected_class: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    is_uncertain: Mapped[bool] = mapped_column(default=False)
    alternate_matches: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    countermeasures: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    drone_prescription: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


# Resilient in-memory stores for offline dev/PostgreSQL disconnects
PEST_REFERENCE_STORE: Dict[str, Dict[str, Any]] = {}
PEST_DIAGNOSES_STORE: Dict[str, Dict[str, Any]] = {}

def init_pest_reference_store():
    """Initializes in-memory reference store from PEST_REFERENCE_DATA seed."""
    from app.seeds.pest_reference_data import PEST_REFERENCE_DATA
    if not PEST_REFERENCE_STORE:
        for idx, item in enumerate(PEST_REFERENCE_DATA):
            pid = str(uuid.uuid5(uuid.NAMESPACE_DNS, item["pest_name"]))
            entry = dict(item)
            entry["id"] = pid
            entry["created_at"] = datetime.now(timezone.utc).isoformat()
            PEST_REFERENCE_STORE[item["pest_name"]] = entry

init_pest_reference_store()
