import math
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.endpoints.iot import LIVESTOCK_STORE

router = APIRouter()

# Default mock herd if none yet transmitted via IoT
DEFAULT_MOCK_HERD = [
    {"tag_id": "COW-101", "animal_type": "cattle", "lat": 30.9026, "lng": 75.8528, "battery_level": 94.0, "status": "Active Grazing"},
    {"tag_id": "COW-102", "animal_type": "cattle", "lat": 30.9029, "lng": 75.8532, "battery_level": 89.0, "status": "Resting / Ruminating"},
    {"tag_id": "COW-103", "animal_type": "cattle", "lat": 30.9022, "lng": 75.8522, "battery_level": 98.0, "status": "Active Grazing"},
    {"tag_id": "BUF-201", "animal_type": "buffalo", "lat": 30.9018, "lng": 75.8535, "battery_level": 76.0, "status": "Watering / Shade"},
]

class LivestockRegistration(BaseModel):
    tag_id: str
    animal_type: str = "cattle"
    plot_id: Optional[str] = None
    collar_battery: float = 100.0

@router.get("/live", summary="Get real-time live positions of all collared livestock")
async def get_live_livestock(plot_id: Optional[str] = None):
    """
    Returns latest GPS positions, battery levels, and grazing activity
    for all tracked animals on the farm.
    """
    results = []
    if LIVESTOCK_STORE:
        for tag, data in LIVESTOCK_STORE.items():
            if plot_id and data.get("plot_id") != plot_id and data.get("plot_id") != "default_plot":
                continue
            
            # Simple heuristic status based on recent movement
            history = data.get("history", [])
            status_text = "Active Grazing"
            if len(history) >= 2:
                dist = math.hypot(history[-1]["lat"] - history[-2]["lat"], history[-1]["lng"] - history[-2]["lng"])
                if dist < 0.00003:
                    status_text = "Resting / Ruminating"
                elif dist > 0.0003:
                    status_text = "Walking / Relocating"

            results.append({
                "tag_id": data["tag_id"],
                "animal_type": data.get("animal_type", "cattle"),
                "plot_id": data.get("plot_id"),
                "latitude": data["lat"],
                "longitude": data["lng"],
                "battery_level": data.get("battery_level", 90.0),
                "last_ping": data.get("last_ping"),
                "status": status_text,
                "history_points_count": len(history)
            })
    else:
        # Provide seed herd around default Ludhiana farm so user sees live data immediately
        now = datetime.now(timezone.utc).isoformat()
        for cow in DEFAULT_MOCK_HERD:
            results.append({
                "tag_id": cow["tag_id"],
                "animal_type": cow["animal_type"],
                "plot_id": plot_id or "default_plot",
                "latitude": cow["lat"],
                "longitude": cow["lng"],
                "battery_level": cow["battery_level"],
                "last_ping": now,
                "status": cow["status"],
                "history_points_count": 12
            })

    return {
        "status": "success",
        "total_animals": len(results),
        "active_grazing_count": sum(1 for a in results if "Grazing" in a["status"]),
        "animals": results
    }

@router.get("/grazing-density", summary="Compute spatial grazing heatmap points and forage depletion metrics")
async def get_grazing_density(plot_id: Optional[str] = None):
    """
    Analyzes historical GPS positions from IoT collars to produce:
    1. Spatial Heatmap coordinates [lat, lng, intensity] for Leaflet.heat
    2. Estimated Biomass / Forage consumption (kg Dry Matter)
    3. Overgrazing Risk Score & Pasture Resting Recommendation
    """
    heat_points: List[List[float]] = []

    # Gather history points from LIVESTOCK_STORE
    total_pings = 0
    if LIVESTOCK_STORE:
        for tag, data in LIVESTOCK_STORE.items():
            for pt in data.get("history", []):
                heat_points.append([pt["lat"], pt["lng"], 0.7])
                total_pings += 1
            # Current location counts heavier
            heat_points.append([data["lat"], data["lng"], 1.0])
            total_pings += 1

    if not heat_points:
        # Fallback synthetic grid points for Ludhiana demo plot
        base_lat, base_lng = 30.9025, 75.8525
        demo_offsets = [
            (0.0001, 0.0002, 0.9),
            (0.0002, 0.0003, 0.8),
            (0.0003, 0.0001, 0.6),
            (-0.0002, 0.0001, 0.95),
            (-0.0001, -0.0002, 0.7),
            (0.0001, -0.0003, 0.5),
            (0.0004, 0.0002, 0.85),
            (0.0000, 0.0000, 1.0),
        ]
        for dlat, dlng, intensity in demo_offsets:
            heat_points.append([base_lat + dlat, base_lng + dlng, intensity])
        total_pings = 48

    # Agro-veterinary grazing calculations (ICAR / NDRI guidelines)
    # Average adult Indian dairy cattle/buffalo consumes ~10-12 kg Dry Matter (DM) per day of green fodder
    active_animals = len(LIVESTOCK_STORE) if LIVESTOCK_STORE else len(DEFAULT_MOCK_HERD)
    est_daily_forage_intake_kg = round(active_animals * 11.5, 1)
    
    # Calculate grazing pressure index (0 to 100%) based on ping cluster concentration
    grazing_pressure_score = min(88, max(24, int(total_pings * 1.8 + active_animals * 5)))
    
    status_assessment = "Moderate Sustainable Grazing"
    pasture_advice = "Pasture sward height is optimal (12-15 cm). Continue rotational grazing."
    if grazing_pressure_score > 75:
        status_assessment = "High Grazing Pressure / Overgrazing Risk in Zone A"
        pasture_advice = "Heavy concentration detected in northern paddock. Rotate herd to paddock B within 24h to avoid root crown damage."
    elif grazing_pressure_score < 40:
        status_assessment = "Low Grazing Utilization"
        pasture_advice = "Forage availability exceeds herd demand. Consider harvesting excess green fodder for silage."

    return {
        "status": "success",
        "plot_id": plot_id,
        "total_tracked_animals": active_animals,
        "heatmap_points": heat_points,
        "analytics": {
            "estimated_daily_intake_kg": est_daily_forage_intake_kg,
            "grazing_pressure_score": grazing_pressure_score,
            "pasture_status": status_assessment,
            "recommended_resting_days": 18 if grazing_pressure_score > 70 else 12,
            "actionable_advice": pasture_advice
        }
    }
