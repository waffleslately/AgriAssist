import logging
from typing import Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.seeds.district_soil_baselines import DISTRICT_SOIL_BASELINES

logger = logging.getLogger("agri_backend.soil")

class SoilService:
    async def get_nearest_soil_sample(
        self,
        db: AsyncSession,
        lat: float,
        lng: float,
        state: Optional[str] = None,
        district: Optional[str] = None,
        max_distance_km: float = 15.0
    ) -> Dict[str, Any]:
        """
        Query nearest Soil Health Card sample via PostGIS spatial distance.
        If distance exceeds max_distance_km or no record exists, fall back to ICAR district benchmark.
        """
        query = text("""
            SELECT 
                id,
                source,
                state,
                district,
                organic_carbon_pct,
                available_nitrogen_kg_ha,
                available_phosphorus_kg_ha,
                available_potassium_kg_ha,
                ph,
                electrical_conductivity,
                zinc_ppm,
                iron_ppm,
                ST_Distance(location::geography, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) / 1000.0 AS distance_km
            FROM soil_health_samples
            WHERE ST_DWithin(location::geography, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :max_distance_meters)
            ORDER BY location <-> ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)
            LIMIT 1;
        """)

        try:
            result = await db.execute(
                query,
                {
                    "lng": lng,
                    "lat": lat,
                    "max_distance_meters": max_distance_km * 1000.0
                }
            )
            row = result.mappings().first()
            if row:
                return {
                    "source": row["source"],
                    "state": row["state"],
                    "district": row["district"],
                    "distance_km": round(float(row["distance_km"]), 2),
                    "organic_carbon_pct": float(row["organic_carbon_pct"]) if row["organic_carbon_pct"] else 0.5,
                    "available_nitrogen_kg_ha": float(row["available_nitrogen_kg_ha"]) if row["available_nitrogen_kg_ha"] else 250.0,
                    "available_phosphorus_kg_ha": float(row["available_phosphorus_kg_ha"]) if row["available_phosphorus_kg_ha"] else 18.0,
                    "available_potassium_kg_ha": float(row["available_potassium_kg_ha"]) if row["available_potassium_kg_ha"] else 280.0,
                    "ph": float(row["ph"]) if row["ph"] else 7.5,
                    "electrical_conductivity": float(row["electrical_conductivity"]) if row["electrical_conductivity"] else 0.3,
                    "is_fallback": False
                }
        except Exception as e:
            logger.warning(f"Spatial soil lookup encountered exception: {e}. Using benchmark fallback.")

        # Fallback to state/district benchmark
        key = f"{state.lower()}_{district.lower()}" if state and district else "default"
        benchmark = DISTRICT_SOIL_BASELINES.get(key, DISTRICT_SOIL_BASELINES["default"])

        return {
            "source": f"ICAR District Benchmark ({benchmark['district']})",
            "state": benchmark["state"],
            "district": benchmark["district"],
            "distance_km": None,
            "organic_carbon_pct": benchmark["organic_carbon_pct"],
            "available_nitrogen_kg_ha": benchmark["available_nitrogen_kg_ha"],
            "available_phosphorus_kg_ha": benchmark["available_phosphorus_kg_ha"],
            "available_potassium_kg_ha": benchmark["available_potassium_kg_ha"],
            "ph": benchmark["ph"],
            "electrical_conductivity": benchmark["electrical_conductivity"],
            "is_fallback": True
        }

soil_service = SoilService()
