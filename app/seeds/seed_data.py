import asyncio
from datetime import date
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.models.soil_health import SoilHealthSample

SAMPLE_SHC_POINTS = [
    # Ludhiana, Punjab
    {
        "source": "shc_portal_grid",
        "state": "Punjab", "district": "Ludhiana",
        "lat": 30.9010, "lng": 75.8573,
        "organic_carbon_pct": 0.54, "available_nitrogen_kg_ha": 270.0,
        "available_phosphorus_kg_ha": 24.5, "available_potassium_kg_ha": 220.0,
        "ph": 7.7, "electrical_conductivity": 0.36, "zinc_ppm": 0.90, "iron_ppm": 4.6
    },
    # Nashik, Maharashtra
    {
        "source": "shc_portal_grid",
        "state": "Maharashtra", "district": "Nashik",
        "lat": 19.9975, "lng": 73.7898,
        "organic_carbon_pct": 0.68, "available_nitrogen_kg_ha": 235.0,
        "available_phosphorus_kg_ha": 19.0, "available_potassium_kg_ha": 350.0,
        "ph": 7.5, "electrical_conductivity": 0.42, "zinc_ppm": 0.75, "iron_ppm": 5.4
    },
    # Indore, Madhya Pradesh
    {
        "source": "shc_portal_grid",
        "state": "Madhya Pradesh", "district": "Indore",
        "lat": 22.7196, "lng": 75.8577,
        "organic_carbon_pct": 0.49, "available_nitrogen_kg_ha": 210.0,
        "available_phosphorus_kg_ha": 15.0, "available_potassium_kg_ha": 390.0,
        "ph": 7.9, "electrical_conductivity": 0.31, "zinc_ppm": 0.62, "iron_ppm": 4.9
    },
    # Guntur, Andhra Pradesh
    {
        "source": "shc_portal_grid",
        "state": "Andhra Pradesh", "district": "Guntur",
        "lat": 16.3067, "lng": 80.4365,
        "organic_carbon_pct": 0.58, "available_nitrogen_kg_ha": 245.0,
        "available_phosphorus_kg_ha": 28.0, "available_potassium_kg_ha": 290.0,
        "ph": 7.8, "electrical_conductivity": 0.45, "zinc_ppm": 0.80, "iron_ppm": 5.1
    }
]

async def seed_database():
    print("Seeding initial Soil Health Card reference points...")
    async with AsyncSessionLocal() as session:
        for pt in SAMPLE_SHC_POINTS:
            wkt_point = f"SRID=4326;POINT({pt['lng']} {pt['lat']})"
            sample = SoilHealthSample(
                source=pt["source"],
                location=wkt_point,
                state=pt["state"],
                district=pt["district"],
                organic_carbon_pct=pt["organic_carbon_pct"],
                available_nitrogen_kg_ha=pt["available_nitrogen_kg_ha"],
                available_phosphorus_kg_ha=pt["available_phosphorus_kg_ha"],
                available_potassium_kg_ha=pt["available_potassium_kg_ha"],
                ph=pt["ph"],
                electrical_conductivity=pt["electrical_conductivity"],
                zinc_ppm=pt["zinc_ppm"],
                iron_ppm=pt["iron_ppm"],
                sample_date=date.today()
            )
            session.add(sample)
        await session.commit()
    print("Seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_database())
