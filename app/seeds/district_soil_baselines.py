"""
Benchmark Soil Health baselines by Indian States and key agricultural districts.
Used as fallback when point-specific Soil Health Card samples are not within 15 km.
"""

DISTRICT_SOIL_BASELINES = {
    # Punjab
    "punjab_ludhiana": {
        "state": "Punjab", "district": "Ludhiana",
        "organic_carbon_pct": 0.52, "available_nitrogen_kg_ha": 265.0,
        "available_phosphorus_kg_ha": 22.0, "available_potassium_kg_ha": 210.0,
        "ph": 7.8, "electrical_conductivity": 0.35, "zinc_ppm": 0.85, "iron_ppm": 4.5
    },
    # Maharashtra
    "maharashtra_nashik": {
        "state": "Maharashtra", "district": "Nashik",
        "organic_carbon_pct": 0.65, "available_nitrogen_kg_ha": 240.0,
        "available_phosphorus_kg_ha": 18.0, "available_potassium_kg_ha": 340.0,
        "ph": 7.6, "electrical_conductivity": 0.40, "zinc_ppm": 0.70, "iron_ppm": 5.2
    },
    # Madhya Pradesh
    "madhya_pradesh_indore": {
        "state": "Madhya Pradesh", "district": "Indore",
        "organic_carbon_pct": 0.48, "available_nitrogen_kg_ha": 215.0,
        "available_phosphorus_kg_ha": 14.5, "available_potassium_kg_ha": 380.0,
        "ph": 7.9, "electrical_conductivity": 0.32, "zinc_ppm": 0.60, "iron_ppm": 4.8
    },
    # Default National Benchmark (All-India Average)
    "default": {
        "state": "All India", "district": "Benchmark Average",
        "organic_carbon_pct": 0.50, "available_nitrogen_kg_ha": 250.0,
        "available_phosphorus_kg_ha": 16.0, "available_potassium_kg_ha": 280.0,
        "ph": 7.5, "electrical_conductivity": 0.30, "zinc_ppm": 0.65, "iron_ppm": 5.0
    }
}
