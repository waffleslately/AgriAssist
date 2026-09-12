from typing import Dict, Any, Optional
from app.seeds.pest_cibrc_guidelines import PEST_CIBRC_GUIDELINES, DGCA_DRONE_SPRAY_SOP

class PestControlEngine:
    def diagnose_and_prescribe(
        self,
        crop_name: str,
        pest_key: str,
        severity_observed_pct: float,
        area_acres: float = 1.0,
        drone_spray_requested: bool = True
    ) -> Dict[str, Any]:
        """
        Diagnoses pest or disease, evaluates Economic Threshold Level (ETL),
        and generates CIBRC-compliant IPM control measures + DGCA-aligned drone spray prescription.
        """
        crop = crop_name.lower().strip()
        crop_pests = PEST_CIBRC_GUIDELINES.get(crop, {})
        
        # Fallback to general pest entry if not found
        pest_data = crop_pests.get(pest_key.lower().strip())
        if not pest_data:
            # Look up first available or default
            if crop_pests:
                first_key = list(crop_pests.keys())[0]
                pest_data = crop_pests[first_key]
            else:
                pest_data = {
                    "name": "General Foliar Pest / Caterpillar",
                    "scientific_name": "Lepidoptera spp.",
                    "etl": "5-10% foliar damage",
                    "cultural_measures": ["Erect pheromone / light traps @ 4 per acre."],
                    "biological_control": {
                        "name": "Neem Oil 1500 ppm",
                        "dosage_per_acre": "1000 ml in water",
                        "timing": "Evening spray"
                    },
                    "chemical_control": {
                        "active_ingredient": "Emamectin Benzoate 5% SG",
                        "trade_examples": "Proclaim",
                        "dosage_knapsack_per_acre": "88 g in 150-200 L water",
                        "drone_dosage_per_acre": "88 g in 10 L water",
                        "waiting_period_days": 14
                    }
                }

        # Check Economic Threshold Level (ETL)
        # Severity >= 10% generally implies ETL breach in Indian guidelines
        etl_breached = severity_observed_pct >= 8.0

        # Drone Prescription Parameters
        chem = pest_data["chemical_control"]
        drone_sop = DGCA_DRONE_SPRAY_SOP.copy()
        
        total_drone_water_litres = round(drone_sop["water_volume_litres_per_acre"] * area_acres, 1)

        drone_prescription = {
            "applicable": drone_spray_requested,
            "target_chemical": chem["active_ingredient"],
            "drone_water_volume_litres": total_drone_water_litres,
            "water_volume_per_acre": f"{drone_sop['water_volume_litres_per_acre']} L/acre",
            "chemical_rate_per_acre": chem["drone_dosage_per_acre"],
            "flight_parameters": {
                "flight_altitude_meters_above_crop": drone_sop["flight_altitude_meters_above_canopy"],
                "flight_speed_m_per_s": drone_sop["flight_speed_m_per_s"],
                "swath_width_meters": drone_sop["swath_width_meters"],
                "nozzle_specification": drone_sop["droplet_size_microns"]
            },
            "flight_safety_limits": drone_sop["weather_constraints"]
        }

        # Bilingual Advice Cards
        en_lines = [
            f"🐛 Pest Diagnosis: {pest_data['name']} ({pest_data.get('scientific_name', '')})",
            f"⚠️ Severity Level: {severity_observed_pct}% infestation. ETL Status: {'🚨 BREACHED - Immediate Spray Required' if etl_breached else 'ℹ️ Below Economic Threshold - Monitor field'}",
            f"📌 ETL Standard: {pest_data['etl']}",
            "",
            "1️⃣ Cultural / Mechanical Control:",
        ]
        for m in pest_data["cultural_measures"]:
            en_lines.append(f" • {m}")

        bio = pest_data["biological_control"]
        en_lines.extend([
            "",
            "2️⃣ Biological Control:",
            f" • Product: {bio['name']} @ {bio['dosage_per_acre']}",
            f" • Timing: {bio['timing']}",
            "",
            "3️⃣ Chemical Treatment (CIBRC Approved):",
            f" • Active: {chem['active_ingredient']} ({chem['trade_examples']})",
            f" • Knapsack Dose: {chem['dosage_knapsack_per_acre']}",
            f" • Drone ULV Dose: {chem['drone_dosage_per_acre']}",
            f" • Safety Pre-Harvest Interval (PHI): {chem['waiting_period_days']} days"
        ])
        if drone_spray_requested:
            en_lines.extend([
                "",
                "🚁 Drone Spray Mission Plan:",
                f" • Water: {total_drone_water_litres} Litres total for {area_acres} acres (10 L/acre)",
                f" • Altitude: {drone_sop['flight_altitude_meters_above_canopy']}m | Speed: {drone_sop['flight_speed_m_per_s']} m/s | Anti-drift nozzle"
            ])

        # Hindi Message
        hi_lines = [
            f"🐛 कीट / रोग निदान: {pest_data['name']}",
            f"⚠️ प्रकोप स्तर: {severity_observed_pct}%। ईटीएल स्थिति: {'🚨 आर्थिक सीमा पार (तुरंत नियंत्रण आवश्यक)' if etl_breached else 'ℹ️ सीमा से कम (निगरानी रखें)'}",
            f"📌 आर्थिक सीमा (ETL): {pest_data['etl']}",
            "",
            "1️⃣ यांत्रिक / जैविक उपाय:",
        ]
        for m in pest_data["cultural_measures"]:
            hi_lines.append(f" • {m}")
        hi_lines.extend([
            f" • जैविक कीटनाशक: {bio['name']} की {bio['dosage_per_acre']} मात्रा का प्रयोग करें।",
            "",
            "2️⃣ रासायनिक नियंत्रण (CIBRC अनुमोदित):",
            f" • रसायन: {chem['active_ingredient']} ({chem['trade_examples']})",
            f" • साधारण स्प्रेयर खुराक: {chem['dosage_knapsack_per_acre']}",
            f" • ड्रोन स्प्रेयर खुराक: {chem['drone_dosage_per_acre']}",
            f" • तुड़ाई से पहले सुरक्षित अंतर (PHI): {chem['waiting_period_days']} दिन"
        ])
        if drone_spray_requested:
            hi_lines.extend([
                "",
                "🚁 ड्रोन छिड़काव निर्देश (DGCA मानक):",
                f" • कुल पानी: {area_acres} एकड़ के लिए {total_drone_water_litres} लीटर पानी (10 लीटर प्रति एकड़)।",
                f" • ड्रोन ऊंचाई: फसल से {drone_sop['flight_altitude_meters_above_canopy']} मीटर ऊपर | गति: {drone_sop['flight_speed_m_per_s']} मीटर/सेकंड।"
            ])

        return {
            "crop": crop_name,
            "pest_name": pest_data["name"],
            "scientific_name": pest_data.get("scientific_name"),
            "severity_observed_pct": severity_observed_pct,
            "economic_threshold_breached": etl_breached,
            "etl_guideline": pest_data["etl"],
            "ipm_measures": {
                "cultural": pest_data["cultural_measures"],
                "biological": pest_data["biological_control"],
                "chemical": chem
            },
            "drone_spray_prescription": drone_prescription,
            "localized_advice": {
                "en": "\n".join(en_lines),
                "hi": "\n".join(hi_lines)
            }
        }

pest_control_engine = PestControlEngine()
