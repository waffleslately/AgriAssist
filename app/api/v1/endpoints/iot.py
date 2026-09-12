import random
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()

# In-memory store for high-throughput live IoT telemetry & fallback when DB is in dev simulation
# Structure: { tag_id: { "tag_id": str, "animal_type": str, "lat": float, "lng": float, "battery": float, "last_ping": iso_str, "plot_id": str, "history": [...] } }
LIVESTOCK_STORE: Dict[str, Dict[str, Any]] = {}

class TelemetryPayload(BaseModel):
    tag_id: str = Field(..., description="Unique collar device or RFID tag ID, e.g. COW-101")
    animal_type: str = Field(default="cattle", description="cattle, sheep, goat, buffalo")
    latitude: float = Field(..., description="Current GPS latitude")
    longitude: float = Field(..., description="Current GPS longitude")
    battery_level: float = Field(default=95.0, description="Collar battery percentage (0-100)")
    plot_id: Optional[str] = Field(default=None, description="Plot ID where pasture is allocated")
    timestamp: Optional[str] = None

@router.post("/telemetry", summary="Ingest live GPS & battery telemetry from animal IoT collar")
async def ingest_collar_telemetry(payload: TelemetryPayload):
    """
    Ingests real-time IoT GPS telemetry from livestock tracking collars or ear tags.
    Maintains time-series historical GPS pings for grazing heatmaps and boundary analysis.
    """
    now = datetime.now(timezone.utc).isoformat()
    ping_time = payload.timestamp or now

    tag = payload.tag_id.strip()

    if tag not in LIVESTOCK_STORE:
        LIVESTOCK_STORE[tag] = {
            "tag_id": tag,
            "animal_type": payload.animal_type,
            "plot_id": payload.plot_id or "default_plot",
            "lat": payload.latitude,
            "lng": payload.longitude,
            "battery_level": payload.battery_level,
            "last_ping": ping_time,
            "history": []
        }
    else:
        record = LIVESTOCK_STORE[tag]
        record["lat"] = payload.latitude
        record["lng"] = payload.longitude
        record["battery_level"] = payload.battery_level
        record["last_ping"] = ping_time
        if payload.plot_id:
            record["plot_id"] = payload.plot_id

    # Append to recent history (capped at 500 pings per collar to maintain performance)
    LIVESTOCK_STORE[tag]["history"].append({
        "lat": payload.latitude,
        "lng": payload.longitude,
        "timestamp": ping_time
    })
    if len(LIVESTOCK_STORE[tag]["history"]) > 500:
        LIVESTOCK_STORE[tag]["history"] = LIVESTOCK_STORE[tag]["history"][-500:]

    return {
        "status": "success",
        "tag_id": tag,
        "recorded_at": ping_time,
        "current_position": [payload.latitude, payload.longitude],
        "battery_level": payload.battery_level
    }

class SimulateRequest(BaseModel):
    center_lat: Optional[float] = 30.9025
    center_lng: Optional[float] = 75.8525
    herd_size: Optional[int] = 5
    plot_id: Optional[str] = "default_plot"

@router.post("/simulate-step", summary="Advance animal movement step inside pasture (IoT Simulator)")
async def simulate_iot_step(payload: SimulateRequest):
    """
    Advances a simulated grazing step for the herd:
    - Moves each animal with a realistic wandering Brownian step (~3-10m)
    - Drains collar battery realistically by 0.05%
    - Appends GPS ping to history for real-time heatmap expansion
    """
    clat = payload.center_lat or 30.9025
    clng = payload.center_lng or 75.8525
    now = datetime.now(timezone.utc).isoformat()

    # If store is empty, seed with herd_size animals
    if not LIVESTOCK_STORE:
        species_list = ["cattle", "cattle", "cattle", "buffalo", "sheep"]
        for i in range(1, (payload.herd_size or 5) + 1):
            tag = f"LIVESTOCK-{100 + i}"
            sp = species_list[(i - 1) % len(species_list)]
            init_lat = clat + random.uniform(-0.0008, 0.0008)
            init_lng = clng + random.uniform(-0.0008, 0.0008)
            LIVESTOCK_STORE[tag] = {
                "tag_id": tag,
                "animal_type": sp,
                "plot_id": payload.plot_id,
                "lat": init_lat,
                "lng": init_lng,
                "battery_level": round(random.uniform(85.0, 99.0), 1),
                "last_ping": now,
                "history": [{"lat": init_lat, "lng": init_lng, "timestamp": now}]
            }

    updated = []
    for tag, animal in LIVESTOCK_STORE.items():
        # Grazing walk step: ~0.00008 to 0.00015 degrees (~8-15m)
        dlat = random.uniform(-0.00012, 0.00012)
        dlng = random.uniform(-0.00012, 0.00012)
        
        # Keep animals within ~200m radius of center
        new_lat = animal["lat"] + dlat
        new_lng = animal["lng"] + dlng
        if abs(new_lat - clat) > 0.0018:
            new_lat = clat + (0.0012 if new_lat > clat else -0.0012)
        if abs(new_lng - clng) > 0.0018:
            new_lng = clng + (0.0012 if new_lng > clng else -0.0012)

        animal["lat"] = round(new_lat, 6)
        animal["lng"] = round(new_lng, 6)
        animal["battery_level"] = max(5.0, round(animal["battery_level"] - random.uniform(0.01, 0.05), 1))
        animal["last_ping"] = now
        animal["history"].append({"lat": animal["lat"], "lng": animal["lng"], "timestamp": now})
        if len(animal["history"]) > 500:
            animal["history"] = animal["history"][-500:]

        updated.append({
            "tag_id": tag,
            "animal_type": animal["animal_type"],
            "lat": animal["lat"],
            "lng": animal["lng"],
            "battery_level": animal["battery_level"]
        })

    return {
        "status": "success",
        "message": f"Simulated 1 grazing step for {len(updated)} animals",
        "timestamp": now,
        "herd": updated
    }

@router.get("/status", summary="Get IoT collar gateway status & active tag count")
async def get_iot_status():
    return {
        "status": "online",
        "total_active_collars": len(LIVESTOCK_STORE),
        "tags": list(LIVESTOCK_STORE.keys())
    }
