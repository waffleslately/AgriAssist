from typing import Dict, Any

class LocalizationService:
    @staticmethod
    def generate_localized_advisory(plan: Dict[str, Any], language: str = "hi") -> Dict[str, str]:
        crop = plan["crop_name"]
        stage = plan["crop_stage"]
        stage_hi = plan["crop_stage_hi"]
        das = plan["days_after_sowing"]
        sched = plan.get("fertilizer_schedule", [])
        weather_hold = plan.get("weather_hold_warning", False)
        rain_reason = plan.get("weather_hold_reason", "")
        irrigation = plan.get("irrigation_advice", "")

        # 1. English Message
        en_lines = [
            f"🌾 Crop Advisory: {crop} | Day {das} ({stage})",
            f"📊 Soil Status: N: {plan['soil_status']['nitrogen']}, P: {plan['soil_status']['phosphorus']}, K: {plan['soil_status']['potassium']}",
            f"🛰️ Satellite NDVI: {plan['satellite_summary']['mean_ndvi']} ({plan['crop_vigor_status']})"
        ]

        if weather_hold:
            en_lines.append(f"⚠️ WEATHER ALERT: {rain_reason}. Delay broadcasting top-dressing until rain stops.")

        if sched:
            en_lines.append("🌿 Recommended Fertilizer Application:")
            for item in sched:
                en_lines.append(
                    f" - {item['fertilizer']}: {item['quantity_kg_per_acre']} kg/acre "
                    f"({item['bags_per_acre']} bags/acre) | {item['instructions']}"
                )
        else:
            en_lines.append("🌿 Fertilizer Application: No chemical fertilizer application required at this stage.")

        en_lines.append(f"💧 Irrigation: {irrigation}")
        en_text = "\n".join(en_lines)

        # 2. Hindi Message
        hi_lines = [
            f"🌾 फसल सलाह: {crop} | बुवाई के {das} दिन ({stage_hi})",
            f"📊 मृदा स्वास्थ्य: नाइट्रोजन: {plan['soil_status']['nitrogen']}, फास्फोरस: {plan['soil_status']['phosphorus']}, पोटाश: {plan['soil_status']['potassium']}",
            f"🛰️ उपग्रह NDVI: {plan['satellite_summary']['mean_ndvi']} ({plan['crop_vigor_status']})"
        ]

        if weather_hold:
            hi_lines.append(f"⚠️ मौसम चेतावनी: {rain_reason}। बारिश रुकने और खेत से पानी निकलने तक खाद का छिड़काव रोकें।")

        if sched:
            hi_lines.append("🌿 अनुशंसित खाद की मात्रा:")
            for item in sched:
                fert_name = item['fertilizer']
                if "Urea" in fert_name:
                    fert_hi = "यूरिया (Urea)"
                elif "DAP" in fert_name:
                    fert_hi = "डीएपी (DAP)"
                elif "MOP" in fert_name:
                    fert_hi = "एमओपी पोटाश (MOP)"
                else:
                    fert_hi = fert_name
                hi_lines.append(f" - {fert_hi}: {item['quantity_kg_per_acre']} किग्रा प्रति एकड़ ({item['bags_per_acre']} बोरी प्रति एकड़)")
        else:
            hi_lines.append("🌿 खाद: इस अवस्था में रासायनिक खाद डालने की आवश्यकता नहीं है।")

        if "Skip irrigation" in irrigation:
            irr_hi = "बारिश की संभावना के कारण अभी सिंचाई रोक दें।"
        elif "Immediate irrigation" in irrigation:
            irr_hi = "मिट्टी में नमी कम है। खाद देने से पहले हल्की सिंचाई करें।"
        else:
            irr_hi = "खेत में नमी सामान्य है, नियमित चक्र अनुसार पानी दें।"
        hi_lines.append(f"💧 सिंचाई सलाह: {irr_hi}")

        hi_text = "\n".join(hi_lines)

        return {
            "en": en_text,
            "hi": hi_text
        }

localization_service = LocalizationService()
