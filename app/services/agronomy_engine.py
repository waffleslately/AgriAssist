from datetime import date
from typing import Dict, Any, List
import math

from app.seeds.crop_guidelines import CROP_GUIDELINES

class AgronomyEngine:
    @staticmethod
    def classify_nutrient(val: float, low_threshold: float, high_threshold: float) -> str:
        if val < low_threshold:
            return "Low"
        elif val > high_threshold:
            return "High"
        return "Medium"

    def calculate_plan(
        self,
        crop_name: str,
        sowing_date: date,
        soil_metrics: Dict[str, Any],
        satellite_metrics: Dict[str, Any],
        weather_metrics: Dict[str, Any],
        area_acres: float = 1.0,
        current_date: date = None
    ) -> Dict[str, Any]:
        if current_date is None:
            current_date = date.today()

        crop_key = crop_name.lower().strip()
        crop_meta = CROP_GUIDELINES.get(crop_key, CROP_GUIDELINES["wheat"])
        rdf = crop_meta["rdf_kg_per_acre"]

        das = max(0, (current_date - sowing_date).days)

        # 1. Classify Soil Health Card N-P-K status
        n_val = soil_metrics.get("available_nitrogen_kg_ha", 250.0)
        p_val = soil_metrics.get("available_phosphorus_kg_ha", 18.0)
        k_val = soil_metrics.get("available_potassium_kg_ha", 280.0)

        n_status = self.classify_nutrient(n_val, 280.0, 560.0)
        p_status = self.classify_nutrient(p_val, 23.0, 56.0)
        k_status = self.classify_nutrient(k_val, 140.0, 330.0)

        # 2. STCR Adjustment factors (+25% for Low, 0% for Medium, -25% for High)
        adj_map = {"Low": 1.25, "Medium": 1.00, "High": 0.75}
        target_n_acre = rdf["N"] * adj_map[n_status]
        target_p_acre = rdf["P"] * adj_map[p_status]
        target_k_acre = rdf["K"] * adj_map[k_status]

        # 3. Find current growth stage
        stages = crop_meta["growth_stages"]
        current_stage = stages[-1]
        for st in stages:
            if st["min_das"] <= das <= st["max_das"]:
                current_stage = st
                break
        
        # If DAS is past all defined stages (crop beyond known range), use last applicable 
        # non-zero nitrogen stage for a final top-dress advisory
        if das > stages[-1]["max_das"]:
            # Find last stage with any nutrient split defined
            applicable = [s for s in stages if s["n_pct"] > 0 or s["p_pct"] > 0 or s["k_pct"] > 0]
            if applicable:
                current_stage = applicable[-1]

        # 4. Check Weather Guard
        heavy_rain = weather_metrics.get("heavy_rain_warning", False)
        rain_mm = weather_metrics.get("precipitation_48h_mm", 0.0)

        # 5. Check NDVI vigor
        mean_ndvi = satellite_metrics.get("mean_ndvi", 0.55)
        vigor_status = "Healthy"
        vigor_alert = None
        if das > 20 and mean_ndvi < 0.38:
            vigor_status = "Stunted / Low Vigor"
            vigor_alert = "NDVI indicates vegetative stress. Consider applying 19:19:19 NPK foliar spray (1 kg/acre in 150L water) or Zinc Sulphate (21% Zn @ 5 kg/acre)."

        # 6. Calculate Stage Fertilizer Quantities
        fertilizer_schedule: List[Dict[str, Any]] = []

        if current_stage["min_das"] == 0:  # Basal dose
            # Deliver all P via DAP (50kg bag = 18% N, 46% P2O5 -> 9kg N, 23kg P2O5 per bag)
            dap_kg_acre = (target_p_acre / 0.46) if target_p_acre > 0 else 0
            dap_bags_acre = dap_kg_acre / 50.0
            n_from_dap = dap_kg_acre * 0.18

            # Remaining Basal N via Urea (45kg bag = 46% N -> 20.7kg N per bag)
            stage_n_need = target_n_acre * (current_stage["n_pct"] / 100.0)
            remaining_n_acre = max(0.0, stage_n_need - n_from_dap)
            urea_kg_acre = remaining_n_acre / 0.46
            urea_bags_acre = urea_kg_acre / 45.0

            # K via MOP (50kg bag = 60% K2O -> 30kg K2O per bag)
            mop_kg_acre = (target_k_acre / 0.60) if target_k_acre > 0 else 0
            mop_bags_acre = mop_kg_acre / 50.0

            if dap_kg_acre > 0:
                fertilizer_schedule.append({
                    "fertilizer": "DAP (18-46-0)",
                    "quantity_kg_per_acre": round(dap_kg_acre, 1),
                    "bags_per_acre": round(dap_bags_acre, 2),
                    "total_bags_for_plot": round(dap_bags_acre * area_acres, 1),
                    "timing_stage": current_stage["stage"],
                    "instructions": "Broadcast or place below seed depth during land preparation / sowing."
                })
            if urea_kg_acre > 0:
                fertilizer_schedule.append({
                    "fertilizer": "Urea (46% N)",
                    "quantity_kg_per_acre": round(urea_kg_acre, 1),
                    "bags_per_acre": round(urea_bags_acre, 2),
                    "total_bags_for_plot": round(urea_bags_acre * area_acres, 1),
                    "timing_stage": current_stage["stage"],
                    "instructions": "Mix with basal dose during final ploughing."
                })
            if mop_kg_acre > 0:
                fertilizer_schedule.append({
                    "fertilizer": "MOP (60% K2O)",
                    "quantity_kg_per_acre": round(mop_kg_acre, 1),
                    "bags_per_acre": round(mop_bags_acre, 2),
                    "total_bags_for_plot": round(mop_bags_acre * area_acres, 1),
                    "timing_stage": current_stage["stage"],
                    "instructions": "Apply as basal potassium reserve."
                })

        else:  # Top dressing stages
            stage_n_need = target_n_acre * (current_stage["n_pct"] / 100.0)
            if stage_n_need > 0:
                urea_kg_acre = stage_n_need / 0.46
                urea_bags_acre = urea_kg_acre / 45.0
                instr = "Broadcast evenly in the afternoon after light irrigation or when soil has adequate moisture."
                if heavy_rain:
                    instr = f"HOLD APPLICATION: Rain forecast ({rain_mm} mm) in next 48h. Apply after rain passes to avoid nitrogen runoff."

                fertilizer_schedule.append({
                    "fertilizer": "Urea (46% N)",
                    "quantity_kg_per_acre": round(urea_kg_acre, 1),
                    "bags_per_acre": round(urea_bags_acre, 2),
                    "total_bags_for_plot": round(urea_bags_acre * area_acres, 1),
                    "timing_stage": current_stage["stage"],
                    "instructions": instr
                })

        # Irrigation advice based on moisture proxy & rain
        moisture = satellite_metrics.get("soil_moisture_proxy", 0.25)
        if heavy_rain:
            irrigation_advice = f"Skip irrigation: Significant rainfall ({rain_mm} mm) predicted in the next 48 hours."
        elif moisture < 0.15:
            irrigation_advice = "Soil moisture proxy is low. Immediate irrigation recommended before applying any top dressing."
        else:
            irrigation_advice = "Soil moisture is adequate. Maintain normal irrigation rotation."

        return {
            "crop_name": crop_meta["name"],
            "crop_stage": current_stage["stage"],
            "crop_stage_hi": current_stage["name_hi"],
            "days_after_sowing": das,
            "crop_vigor_status": vigor_status,
            "vigor_alert": vigor_alert,
            "soil_status": {
                "nitrogen": n_status,
                "phosphorus": p_status,
                "potassium": k_status
            },
            "weather_hold_warning": heavy_rain,
            "weather_hold_reason": f"Expected rain of {rain_mm} mm in next 48h" if heavy_rain else None,
            "fertilizer_schedule": fertilizer_schedule,
            "irrigation_advice": irrigation_advice,
            "satellite_summary": {
                "mean_ndvi": mean_ndvi,
                "soil_moisture": moisture
            }
        }

agronomy_engine = AgronomyEngine()
