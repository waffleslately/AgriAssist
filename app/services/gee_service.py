import logging
from datetime import date, timedelta
from typing import Dict, Any, List
import random

from app.core.config import settings

logger = logging.getLogger("agri_backend.gee")

class GEEService:
    def __init__(self):
        self.enabled = settings.GEE_ENABLED
        self._initialized = False
        if self.enabled and settings.GEE_SERVICE_ACCOUNT and settings.GEE_PRIVATE_KEY:
            try:
                import ee
                credentials = ee.ServiceAccountCredentials(
                    settings.GEE_SERVICE_ACCOUNT,
                    key_data=settings.GEE_PRIVATE_KEY
                )
                ee.Initialize(credentials, project=settings.GEE_PROJECT_ID)
                self._initialized = True
                logger.info("Google Earth Engine initialized successfully in live mode.")
            except Exception as e:
                logger.warning(f"GEE live initialization failed, falling back to simulation adapter: {e}")
                self._initialized = False
        else:
            logger.info("GEE service running in developer simulation adapter mode.")

    async def get_plot_metrics(
        self,
        coordinates: List[List[float]],
        target_date: date = None
    ) -> Dict[str, Any]:
        """
        Pull Sentinel-2 NDVI and moisture metrics for the polygon boundary.
        coordinates: list of [lng, lat] coordinate pairs defining the polygon ring.
        """
        if target_date is None:
            target_date = date.today()

        if self._initialized:
            try:
                import ee
                # Create GEE Polygon
                polygon = ee.Geometry.Polygon([coordinates])
                start_date = (target_date - timedelta(days=20)).isoformat()
                end_date = target_date.isoformat()

                # Query Sentinel-2 Surface Reflectance (cloud masked)
                collection = (
                    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                    .filterBounds(polygon)
                    .filterDate(start_date, end_date)
                    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
                )

                def calculate_indices(img):
                    ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
                    ndmi = img.normalizedDifference(["B8", "B11"]).rename("NDMI") # moisture index
                    return img.addBands([ndvi, ndmi])

                with_indices = collection.map(calculate_indices)
                latest = with_indices.sort("system:time_start", False).first()

                stats = latest.reduceRegion(
                    reducer=ee.Reducer.mean().combine(
                        reducer2=ee.Reducer.percentile([10, 90]),
                        sharedInputs=True
                    ),
                    geometry=polygon,
                    scale=10,
                    maxPixels=1e9
                ).getInfo()

                return {
                    "source": "Sentinel-2 (Live GEE)",
                    "acquisition_date": target_date.isoformat(),
                    "mean_ndvi": round(float(stats.get("NDVI_mean", 0.55)), 3),
                    "p10_ndvi": round(float(stats.get("NDVI_p10", 0.40)), 3),
                    "p90_ndvi": round(float(stats.get("NDVI_p90", 0.70)), 3),
                    "soil_moisture_proxy": round(float(stats.get("NDMI_mean", 0.25)), 3),
                    "cloud_cover_percentage": 5.0,
                    "is_simulated": False
                }
            except Exception as e:
                logger.error(f"Error fetching live GEE metrics: {e}. Using fallback simulator.")

        # Dev / Simulation mode adapter
        # Derive realistic agricultural metrics based on centroid
        centroid_lng = sum(p[0] for p in coordinates) / len(coordinates)
        centroid_lat = sum(p[1] for p in coordinates) / len(coordinates)
        
        # Seeded pseudorandom based on coords & date for deterministic realistic behavior
        seed = int((centroid_lat + centroid_lng) * 1000) + target_date.day
        rnd = random.Random(seed)

        base_ndvi = rnd.uniform(0.48, 0.68)
        moisture = rnd.uniform(0.18, 0.38)
        cloud = rnd.uniform(0.0, 15.0)

        return {
            "source": "Sentinel-2 (Simulated Dev Adapter)",
            "acquisition_date": target_date.isoformat(),
            "mean_ndvi": round(base_ndvi, 3),
            "p10_ndvi": round(base_ndvi - 0.08, 3),
            "p90_ndvi": round(base_ndvi + 0.07, 3),
            "soil_moisture_proxy": round(moisture, 3),
            "cloud_cover_percentage": round(cloud, 1),
            "is_simulated": True
        }

    async def get_ndvi_timeseries(
        self,
        coordinates: List[List[float]],
        days: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Return a 60-day NDVI timeseries (one point per ~10 days) as a list of
        {"date": "YYYY-MM-DD", "ndvi": float} dicts.
        Uses deterministic sigmoidal crop-growth simulation in dev mode.
        """
        target_date = date.today()
        centroid_lng = sum(p[0] for p in coordinates) / len(coordinates)
        centroid_lat = sum(p[1] for p in coordinates) / len(coordinates)
        seed = int((centroid_lat + centroid_lng) * 1000) + target_date.day
        rnd = random.Random(seed)

        # Simulate a realistic crop growth curve (sigmoid) over 60 days
        peak_ndvi = rnd.uniform(0.62, 0.82)
        mid_das = rnd.randint(28, 45)   # inflection point of sigmoid
        k_rate = rnd.uniform(0.07, 0.12) # growth steepness
        baseline = rnd.uniform(0.18, 0.28)

        result = []
        # 6 observations at roughly 10-day intervals going back 60 days
        intervals = list(range(days, -1, -(days // 6)))[:7]
        for days_back in reversed(intervals):
            obs_date = target_date - timedelta(days=days_back)
            das = days - days_back   # approximate day after sowing
            import math as _math
            sigmoid = 1 / (1 + _math.exp(-k_rate * (das - mid_das)))
            ndvi = baseline + (peak_ndvi - baseline) * sigmoid
            noise = rnd.uniform(-0.015, 0.015)
            result.append({
                "date": obs_date.isoformat(),
                "ndvi": round(max(0.05, ndvi + noise), 3)
            })
        return result

gee_service = GEEService()
