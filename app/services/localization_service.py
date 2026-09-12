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

        # 1. English
        en_lines = [
            f"🌾 Crop Advisory: {crop.capitalize()} | Day {das} ({stage})",
            f"📊 Soil Health Status: N: {plan['soil_status']['nitrogen']}, P: {plan['soil_status']['phosphorus']}, K: {plan['soil_status']['potassium']}",
            f"🛰️ Satellite NDVI Vigor: {plan['satellite_summary']['mean_ndvi']} ({plan['crop_vigor_status']})"
        ]
        if weather_hold:
            en_lines.append(f"⚠️ WEATHER ALERT: {rain_reason}. Delay broadcasting top-dressing until rain stops.")
        if sched:
            en_lines.append("🌿 Recommended Commercial Fertilizer Application:")
            for item in sched:
                en_lines.append(
                    f" - {item['fertilizer']}: {item['quantity_kg_per_acre']} kg/acre "
                    f"({item['bags_per_acre']} bags/acre) | {item['instructions']}"
                )
        else:
            en_lines.append("🌿 Fertilizer: No chemical fertilizer application required at this stage.")
        en_lines.append(f"💧 Irrigation: {irrigation}")
        en_text = "\n".join(en_lines)

        # 2. Hindi
        hi_lines = [
            f"🌾 फसल सलाह: {crop} | बुवाई के {das} दिन ({stage_hi})",
            f"📊 मृदा स्वास्थ्य: नाइट्रोजन: {plan['soil_status']['nitrogen']}, फास्फोरस: {plan['soil_status']['phosphorus']}, पोटाश: {plan['soil_status']['potassium']}",
            f"🛰️ उपग्रह NDVI स्वास्थ्य: {plan['satellite_summary']['mean_ndvi']} ({plan['crop_vigor_status']})"
        ]
        if weather_hold:
            hi_lines.append(f"⚠️ मौसम चेतावनी: {rain_reason}। बारिश रुकने और खेत से पानी निकलने तक खाद का छिड़काव रोकें।")
        if sched:
            hi_lines.append("🌿 अनुशंसित खाद की मात्रा (व्यावसायिक बोरी):")
            for item in sched:
                fert_name = item['fertilizer']
                fert_hi = "यूरिया (Urea)" if "Urea" in fert_name else ("डीएपी (DAP)" if "DAP" in fert_name else ("एमओपी पोटाश (MOP)" if "MOP" in fert_name else fert_name))
                hi_lines.append(f" - {fert_hi}: {item['quantity_kg_per_acre']} किग्रा प्रति एकड़ ({item['bags_per_acre']} बोरी प्रति एकड़)")
        else:
            hi_lines.append("🌿 खाद: इस अवस्था में रासायनिक खाद डालने की आवश्यकता नहीं है।")

        irr_hi = "बारिश की संभावना के कारण अभी सिंचाई रोक दें।" if "Skip irrigation" in irrigation else ("मिट्टी में नमी कम है। खाद देने से पहले हल्की सिंचाई करें।" if "Immediate irrigation" in irrigation else "खेत में नमी सामान्य है, नियमित चक्र अनुसार पानी दें।")
        hi_lines.append(f"💧 सिंचाई सलाह: {irr_hi}")
        hi_text = "\n".join(hi_lines)

        # 3. Punjabi (ਪੰਜਾਬੀ)
        pa_lines = [
            f"🌾 ਫ਼ਸਲ ਸਲਾਹ: {crop} | ਬਿਜਾਈ ਦੇ {das} ਦਿਨ ({stage})",
            f"📊 ਮਿੱਟੀ ਦੀ ਸਿਹਤ: ਨਾਈਟ੍ਰੋਜਨ: {plan['soil_status']['nitrogen']}, ਫਾਸਫੋਰਸ: {plan['soil_status']['phosphorus']}, ਪੋਟਾਸ਼: {plan['soil_status']['potassium']}",
            f"🛰️ ਸੈਟੇਲਾਈਟ NDVI: {plan['satellite_summary']['mean_ndvi']} ({plan['crop_vigor_status']})"
        ]
        if weather_hold:
            pa_lines.append(f"⚠️ ਮੌਸਮ ਚੇਤਾਵਨੀ: {rain_reason}। ਮੀਂਹ ਰੁਕਣ ਤੱਕ ਯੂਰੀਆ ਦਾ ਛਿੜਕਾਅ ਰੋਕੋ।")
        if sched:
            pa_lines.append("🌿 ਸਿਫਾਰਸ਼ ਕੀਤੀ ਖਾਦ (ਬੋਰੀਆਂ ਪ੍ਰਤੀ ਏਕੜ):")
            for item in sched:
                pa_lines.append(f" - {item['fertilizer']}: {item['quantity_kg_per_acre']} ਕਿੱਲੋ ({item['bags_per_acre']} ਥੈਲੇ/ਏਕੜ)")
        else:
            pa_lines.append("🌿 ਖਾਦ: ਇਸ ਪੜਾਅ ਤੇ ਕਿਸੇ ਰਸਾਇਣਕ ਖਾਦ ਦੀ ਲੋੜ ਨਹੀਂ ਹੈ।")
        pa_lines.append(f"💧 ਸਿੰਚਾਈ ਸਲਾਹ: {irrigation}")
        pa_text = "\n".join(pa_lines)

        # 4. Marathi (मराठी)
        mr_lines = [
            f"🌾 पीक सल्ला: {crop} | पेरणीनंतरचे {das} दिवस ({stage})",
            f"📊 माती परीक्षण स्थिती: नत्र (N): {plan['soil_status']['nitrogen']}, स्फुरद (P): {plan['soil_status']['phosphorus']}, पालाश (K): {plan['soil_status']['potassium']}",
            f"🛰️ सॅटेलाइट NDVI: {plan['satellite_summary']['mean_ndvi']} ({plan['crop_vigor_status']})"
        ]
        if weather_hold:
            mr_lines.append(f"⚠️ हवामान इशारा: {rain_reason}. पाऊस थांबेपर्यंत खत देणे पुढे ढकला.")
        if sched:
            mr_lines.append("🌿 खतांचे शिफारस केलेले प्रमाण:")
            for item in sched:
                mr_lines.append(f" - {item['fertilizer']}: {item['quantity_kg_per_acre']} किलो/एकर ({item['bags_per_acre']} पोती/एकर)")
        else:
            mr_lines.append("🌿 खत: या अवस्थेत रासायनिक खताची गरज नाही.")
        mr_lines.append(f"💧 सिंचन सल्ला: {irrigation}")
        mr_text = "\n".join(mr_lines)

        return {
            "en": en_text,
            "hi": hi_text,
            "pa": pa_text,
            "mr": mr_text
        }

localization_service = LocalizationService()
