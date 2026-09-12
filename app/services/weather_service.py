import logging
from typing import Dict, Any
import httpx

logger = logging.getLogger("agri_backend.weather")

class WeatherService:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"

    async def get_forecast(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Fetch 7-day forecast from Open-Meteo with fallback.
        Checks for heavy rainfall (>15mm in next 48h) to prevent fertilizer leaching.
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "precipitation_probability_max",
                "weathercode"
            ],
            "timezone": "auto"
        }

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                response = await client.get(self.base_url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    daily = data.get("daily", {})
                    precip_list = daily.get("precipitation_sum", [0.0] * 7)
                    
                    # Calculate next 48h rain (today + tomorrow)
                    rain_48h = sum(precip_list[:2]) if len(precip_list) >= 2 else precip_list[0]
                    heavy_rain = rain_48h > 15.0

                    return {
                        "source": "Open-Meteo",
                        "dates": daily.get("time", []),
                        "max_temp": daily.get("temperature_2m_max", [32.0])[0],
                        "min_temp": daily.get("temperature_2m_min", [22.0])[0],
                        "precipitation_48h_mm": round(rain_48h, 1),
                        "heavy_rain_warning": heavy_rain,
                        "raw_daily": daily
                    }
        except Exception as e:
            logger.warning(f"Weather API request failed: {e}. Using resilient climatic fallback.")

        # Resilient fallback forecast
        return {
            "source": "Agri-Weather Baseline Fallback",
            "dates": [],
            "max_temp": 31.5,
            "min_temp": 22.0,
            "precipitation_48h_mm": 2.5,
            "heavy_rain_warning": False,
            "raw_daily": {}
        }

weather_service = WeatherService()
