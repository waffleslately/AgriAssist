import pytest
from app.services.soil_service import soil_service
from app.seeds.district_soil_baselines import DISTRICT_SOIL_BASELINES

@pytest.mark.asyncio
async def test_soil_service_benchmark_fallback():
    class DummyDB:
        async def execute(self, *args, **kwargs):
            raise Exception("No DB connection in unit test")

    result = await soil_service.get_nearest_soil_sample(
        db=DummyDB(),
        lat=30.90,
        lng=75.85,
        state="Punjab",
        district="Ludhiana"
    )

    assert result["is_fallback"] is True
    assert result["state"] == "Punjab"
    assert result["district"] == "Ludhiana"
    assert result["available_nitrogen_kg_ha"] == 265.0
