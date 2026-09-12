import math
import logging
from typing import Dict, Any, List
from app.seeds.crop_reference_ranges import CROP_REFERENCE_RANGES

logger = logging.getLogger("agri_backend.crop_recommender")

class CropRecommender:
    """
    Suitability ranker leveraging the Atharva Ingle Crop Recommendation Dataset (Kaggle).
    Compares farmer's N, P, K, pH and localized climatic metrics against suitable ranges.
    """

    @staticmethod
    def _metric_fit(val: float, ref_range: Dict[str, Any]) -> float:
        """
        Compute fit score between 0.0 and 1.0 for a single metric.
        Perfect match at mean yields 1.0; inside min-max yields 0.75-1.0; outside scales down smoothly.
        """
        if val is None:
            return 0.7  # Neutral default if metric missing

        min_val = ref_range["min"]
        max_val = ref_range["max"]
        mean_val = ref_range.get("mean", (min_val + max_val) / 2.0)
        span = max(1.0, max_val - min_val)

        if min_val <= val <= max_val:
            # Inside ideal reference range
            deviation = abs(val - mean_val) / (span / 2.0)
            return round(1.0 - 0.25 * deviation, 3)
        elif val < min_val:
            # Below ideal range
            deficit = (min_val - val) / span
            return round(max(0.05, 0.75 - deficit * 0.75), 3)
        else:
            # Above ideal range
            excess = (val - max_val) / span
            return round(max(0.05, 0.75 - excess * 0.75), 3)

    def rank_crops(
        self,
        n: float,
        p: float,
        k: float,
        ph: float,
        temperature: float = 24.0,
        humidity: float = 65.0,
        rainfall: float = 85.0,
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rank all 22 reference crops and return top N matches with fit_score and plain-language explanation.
        """
        scored_crops = []

        for crop_key, meta in CROP_REFERENCE_RANGES.items():
            # Calculate component fit scores
            fit_n = self._metric_fit(n, meta["n"])
            fit_p = self._metric_fit(p, meta["p"])
            fit_k = self._metric_fit(k, meta["k"])
            fit_ph = self._metric_fit(ph, meta["ph"])
            fit_temp = self._metric_fit(temperature, meta["temperature"])
            fit_hum = self._metric_fit(humidity, meta["humidity"])
            fit_rain = self._metric_fit(rainfall, meta["rainfall"])

            # Weighted overall fit: Soil NPK/pH = 70%, Climate = 30%
            soil_score = (fit_n * 0.35) + (fit_p * 0.25) + (fit_k * 0.20) + (fit_ph * 0.20)
            climate_score = (fit_temp * 0.40) + (fit_hum * 0.30) + (fit_rain * 0.30)

            overall_fit = round((soil_score * 0.70) + (climate_score * 0.30), 2)

            # Generate plain-language reason "why"
            reasons = []
            if fit_ph >= 0.85:
                reasons.append(f"Soil pH ({ph:.1f}) is ideal")
            if fit_n >= 0.85:
                reasons.append(f"Nitrogen ({n:.0f} kg/ha) matches requirement")
            if fit_p >= 0.85:
                reasons.append(f"Phosphorus ({p:.0f} kg/ha) is in optimum range")
            if fit_k >= 0.85:
                reasons.append(f"Potassium ({k:.0f} kg/ha) is well-suited")

            if not reasons:
                reasons.append("Tolerant to current baseline soil fertility levels")

            why_text = f"Your {', '.join(reasons)}."

            scored_crops.append({
                "crop": crop_key,
                "display_name": meta.get("display_name", crop_key.capitalize()),
                "season": meta.get("season", "general"),
                "fit_score": overall_fit,
                "soil_fit": round(soil_score, 2),
                "climate_fit": round(climate_score, 2),
                "ideal_ranges": {
                    "n": f"{meta['n']['min']}-{meta['n']['max']} kg/ha",
                    "p": f"{meta['p']['min']}-{meta['p']['max']} kg/ha",
                    "k": f"{meta['k']['min']}-{meta['k']['max']} kg/ha",
                    "ph": f"{meta['ph']['min']}-{meta['ph']['max']}"
                },
                "why": why_text
            })

        # Sort descending by fit_score
        scored_crops.sort(key=lambda x: x["fit_score"], reverse=True)
        return scored_crops[:top_n]

crop_recommender = CropRecommender()
