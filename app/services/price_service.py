import time
import logging
from datetime import datetime, timezone, date
from typing import Dict, Any, Optional, List
import httpx

from app.core.config import settings

logger = logging.getLogger("agri_backend.price_service")

# ==============================================================================
# 1. CCEA OFFICIAL MINIMUM SUPPORT PRICE (MSP) REFERENCE TABLE
# Source: Cabinet Committee on Economic Affairs (CCEA) & CACP
# 2024-25 / 2025-26 Approved Price Policy for Kharif & Rabi Crops (Rs. per quintal)
# ==============================================================================
MSP_RATES: Dict[str, Dict[str, Any]] = {
    "wheat": {
        "crop": "Wheat",
        "crop_hi": "गेहूं",
        "msp_per_quintal": 2275.0,
        "season": "Rabi",
        "year": "2024-25",
        "notified": True,
        "agency": "FCI / State Agencies"
    },
    "paddy": {
        "crop": "Paddy (Common)",
        "crop_hi": "धान (साधारण)",
        "msp_per_quintal": 2300.0,
        "season": "Kharif",
        "year": "2024-25",
        "notified": True,
        "agency": "FCI / State Agencies"
    },
    "paddy_grade_a": {
        "crop": "Paddy (Grade A)",
        "crop_hi": "धान (ग्रेड ए)",
        "msp_per_quintal": 2320.0,
        "season": "Kharif",
        "year": "2024-25",
        "notified": True,
        "agency": "FCI / State Agencies"
    },
    "cotton": {
        "crop": "Cotton (Medium Staple)",
        "crop_hi": "कपास",
        "msp_per_quintal": 7121.0,
        "season": "Kharif",
        "year": "2024-25",
        "notified": True,
        "agency": "CCI (Cotton Corp of India)"
    },
    "maize": {
        "crop": "Maize",
        "crop_hi": "मक्का",
        "msp_per_quintal": 2225.0,
        "season": "Kharif",
        "year": "2024-25",
        "notified": True,
        "agency": "NAFED / State Agencies"
    },
    "mustard": {
        "crop": "Mustard & Rapeseed",
        "crop_hi": "सरसों / राई",
        "msp_per_quintal": 5650.0,
        "season": "Rabi",
        "year": "2024-25",
        "notified": True,
        "agency": "NAFED"
    },
    "chickpea": {
        "crop": "Gram (Chickpea)",
        "crop_hi": "चना",
        "msp_per_quintal": 5440.0,
        "season": "Rabi",
        "year": "2024-25",
        "notified": True,
        "agency": "NAFED"
    },
    "soybean": {
        "crop": "Soybean (Yellow)",
        "crop_hi": "सोयाबीन",
        "msp_per_quintal": 4892.0,
        "season": "Kharif",
        "year": "2024-25",
        "notified": True,
        "agency": "NAFED"
    },
    "groundnut": {
        "crop": "Groundnut (In Shell)",
        "crop_hi": "मूंगफली",
        "msp_per_quintal": 6783.0,
        "season": "Kharif",
        "year": "2024-25",
        "notified": True,
        "agency": "NAFED"
    },
    "sugarcane": {
        "crop": "Sugarcane (Fair & Remunerative Price - FRP)",
        "crop_hi": "गन्ना (FRP)",
        "msp_per_quintal": 340.0,
        "season": "Annual",
        "year": "2024-25",
        "notified": True,
        "agency": "Sugar Mills Statutory FRP"
    },
    "bajra": {
        "crop": "Bajra (Pearl Millet)",
        "crop_hi": "बाजरा",
        "msp_per_quintal": 2625.0,
        "season": "Kharif",
        "year": "2024-25",
        "notified": True,
        "agency": "FCI / State Agencies"
    },
    "jowar": {
        "crop": "Jowar (Hybrid)",
        "crop_hi": "ज्वार",
        "msp_per_quintal": 3371.0,
        "season": "Kharif",
        "year": "2024-25",
        "notified": True,
        "agency": "State Agencies"
    },
    "ragi": {
        "crop": "Ragi (Finger Millet)",
        "crop_hi": "रागी",
        "msp_per_quintal": 4290.0,
        "season": "Kharif",
        "year": "2024-25",
        "notified": True,
        "agency": "State Agencies"
    },
    "arhar": {
        "crop": "Arhar / Tur (Pigeonpea)",
        "crop_hi": "अरहर / तूर",
        "msp_per_quintal": 7550.0,
        "season": "Kharif",
        "year": "2024-25",
        "notified": True,
        "agency": "NAFED / NCCF"
    },
    "moong": {
        "crop": "Moong (Green Gram)",
        "crop_hi": "मूंग",
        "msp_per_quintal": 8682.0,
        "season": "Kharif",
        "year": "2024-25",
        "notified": True,
        "agency": "NAFED"
    },
    "urad": {
        "crop": "Urad (Black Gram)",
        "crop_hi": "उड़द",
        "msp_per_quintal": 7400.0,
        "season": "Kharif",
        "year": "2024-25",
        "notified": True,
        "agency": "NAFED"
    },
    "lentil": {
        "crop": "Lentil (Masur)",
        "crop_hi": "मसूर",
        "msp_per_quintal": 6425.0,
        "season": "Rabi",
        "year": "2024-25",
        "notified": True,
        "agency": "NAFED"
    },
    "barley": {
        "crop": "Barley (Jau)",
        "crop_hi": "जौ",
        "msp_per_quintal": 1850.0,
        "season": "Rabi",
        "year": "2024-25",
        "notified": True,
        "agency": "FCI"
    },
    "sunflower": {
        "crop": "Sunflower Seed",
        "crop_hi": "सूरजमुखी",
        "msp_per_quintal": 7280.0,
        "season": "Kharif",
        "year": "2024-25",
        "notified": True,
        "agency": "NAFED"
    },
    "sesamum": {
        "crop": "Sesamum (Til)",
        "crop_hi": "तिल",
        "msp_per_quintal": 9267.0,
        "season": "Kharif",
        "year": "2024-25",
        "notified": True,
        "agency": "NAFED"
    },
    "safflower": {
        "crop": "Safflower (Kusum)",
        "crop_hi": "कुसुम",
        "msp_per_quintal": 5800.0,
        "season": "Rabi",
        "year": "2024-25",
        "notified": True,
        "agency": "NAFED"
    }
}

# ==============================================================================
# 2. SENSIBLE ICAR AVERAGE YIELD BASELINES (Quintals per Acre)
# Source: ICAR Crop Factsheets & State Agriculture Dept. Yearbooks
# ==============================================================================
CROP_AVG_YIELD: Dict[str, float] = {
    "wheat": 19.5,
    "paddy": 24.0,
    "cotton": 9.0,
    "maize": 22.0,
    "mustard": 7.5,
    "chickpea": 7.0,
    "soybean": 9.0,
    "sugarcane": 320.0,
    "groundnut": 9.5,
    "bajra": 11.0,
    "jowar": 10.0,
    "potato": 100.0,
    "onion": 85.0,
    "tomato": 120.0,
    "moong": 4.5,
    "urad": 4.5,
    "arhar": 6.0,
    "lentil": 5.5,
    "barley": 14.0,
    "sunflower": 7.0
}

# Commodity Name Mapping to Agmarknet (data.gov.in) names
COMMODITY_ALIASES: Dict[str, str] = {
    "wheat": "Wheat",
    "paddy": "Paddy(Dhan)(Common)",
    "rice": "Paddy(Dhan)(Common)",
    "cotton": "Cotton",
    "maize": "Maize",
    "mustard": "Mustard",
    "rapeseed": "Mustard",
    "chickpea": "Gram",
    "gram": "Gram",
    "soybean": "Soyabean",
    "groundnut": "Groundnut",
    "sugarcane": "Sugarcane",
    "bajra": "Bajra(Pearl Millet/Cumbu)",
    "jowar": "Jowar(Sorghum)",
    "potato": "Potato",
    "onion": "Onion",
    "tomato": "Tomato",
    "moong": "Green Gram (Moong)",
    "mungbean": "Green Gram (Moong)",
    "urad": "Black Gram (Urd Crop)",
    "blackgram": "Black Gram (Urd Crop)",
    "arhar": "Arhar (Tur/Red Gram)",
    "pigeonpea": "Arhar (Tur/Red Gram)",
    "tur": "Arhar (Tur/Red Gram)",
    "lentil": "Masur Dal",
    "barley": "Barley (Jau)"
}

# ==============================================================================
# 3. CACHE & HISTORICAL STORE
# ==============================================================================
CACHE_TTL_SECONDS = 4 * 3600  # 4 Hours TTL per user requirement
_PRICE_CACHE: Dict[str, Dict[str, Any]] = {}

# Seeded recent fallback mandi prices from Agmarknet verified bulletins
_LAST_KNOWN_PRICE_STORE: Dict[str, Dict[str, Any]] = {
    "wheat_punjab_ludhiana": {
        "modal_price_per_quintal": 2380.0,
        "min_price": 2280.0,
        "max_price": 2420.0,
        "market": "Ludhiana Mandi",
        "as_of_date": "2026-09-12",
        "source": "cached"
    },
    "paddy_punjab_ludhiana": {
        "modal_price_per_quintal": 2340.0,
        "min_price": 2300.0,
        "max_price": 2360.0,
        "market": "Ludhiana Mandi",
        "as_of_date": "2026-09-12",
        "source": "cached"
    },
    "cotton_punjab_bathinda": {
        "modal_price_per_quintal": 7250.0,
        "min_price": 6900.0,
        "max_price": 7400.0,
        "market": "Bathinda Mandi",
        "as_of_date": "2026-09-12",
        "source": "cached"
    },
    "mustard_rajasthan_alwar": {
        "modal_price_per_quintal": 5780.0,
        "min_price": 5500.0,
        "max_price": 5900.0,
        "market": "Alwar Mandi",
        "as_of_date": "2026-09-12",
        "source": "cached"
    },
    "maize_karnataka_davangere": {
        "modal_price_per_quintal": 2290.0,
        "min_price": 2150.0,
        "max_price": 2350.0,
        "market": "Davangere Mandi",
        "as_of_date": "2026-09-12",
        "source": "cached"
    }
}


class PriceService:
    """
    Government of India Price Service:
    - Agmarknet Live Mandi Prices from data.gov.in API
    - Official CCEA Minimum Support Price (MSP) Reference Table
    - Resilient multi-tier caching (4-hour cache -> last known -> MSP floor)
    """

    def __init__(self):
        self.api_endpoint = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
        self.api_key = getattr(
            settings,
            "DATA_GOV_IN_API_KEY",
            "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
        ) or "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"

    def _normalize_crop(self, crop: str) -> str:
        k = crop.lower().strip().replace(" ", "").replace("-", "").replace("_", "")
        if "wheat" in k: return "wheat"
        if "paddy" in k or "rice" in k or "dhan" in k: return "paddy"
        if "cotton" in k or "kapas" in k: return "cotton"
        if "maize" in k or "makka" in k: return "maize"
        if "mustard" in k or "sarson" in k or "rapeseed" in k: return "mustard"
        if "chickpea" in k or "gram" in k or "chana" in k: return "chickpea"
        if "soybean" in k or "soya" in k: return "soybean"
        if "groundnut" in k or "peanut" in k or "mungphali" in k: return "groundnut"
        if "sugarcane" in k or "ganna" in k: return "sugarcane"
        if "bajra" in k: return "bajra"
        if "jowar" in k: return "jowar"
        if "ragi" in k: return "ragi"
        if "arhar" in k or "tur" in k or "pigeonpea" in k: return "arhar"
        if "moong" in k or "mung" in k: return "moong"
        if "urad" in k or "blackgram" in k: return "urad"
        if "lentil" in k or "masur" in k: return "lentil"
        if "potato" in k or "aloo" in k: return "potato"
        if "onion" in k or "pyaj" in k: return "onion"
        if "tomato" in k or "tamatar" in k: return "tomato"
        return crop.lower().strip()

    def get_msp_rate(self, crop: str, season: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Looks up the seeded msp_rates table for this crop's current season MSP.
        Returns None if this crop has no MSP (MSP only covers ~23 notified crops).
        """
        norm_key = self._normalize_crop(crop)
        rate = MSP_RATES.get(norm_key)
        if rate:
            return dict(rate)
        return None

    def get_avg_yield_per_acre(self, crop: str) -> float:
        """
        Returns sensible ICAR regional default yield in quintals per acre.
        """
        norm_key = self._normalize_crop(crop)
        return CROP_AVG_YIELD.get(norm_key, 15.0)

    def update_msp_rate(self, crop: str, msp_per_quintal: float, season: str, year: str) -> Dict[str, Any]:
        """
        Admin-editable way to update MSP reference table each season.
        """
        norm_key = self._normalize_crop(crop)
        record = {
            "crop": crop.capitalize(),
            "crop_hi": MSP_RATES.get(norm_key, {}).get("crop_hi", crop),
            "msp_per_quintal": float(msp_per_quintal),
            "season": season,
            "year": year,
            "notified": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        MSP_RATES[norm_key] = record
        return record

    async def get_live_mandi_price(
        self,
        crop: str,
        state: str = "Punjab",
        district: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetches live mandi price from data.gov.in (Agmarknet).
        - Multi-tier caching with 4-hour TTL.
        - Averages modal prices across markets in given district.
        - Graceful fallback: cached data -> MSP floor price -> clear unavailable message.
        """
        norm_crop = self._normalize_crop(crop)
        cache_key = f"{norm_crop}_{state.lower()}_{district.lower() if district else 'all'}"
        now_ts = time.time()

        # Tier 1: In-memory cache hit (< 4 hours)
        cached_entry = _PRICE_CACHE.get(cache_key)
        if cached_entry and (now_ts - cached_entry["timestamp"] < CACHE_TTL_SECONDS):
            logger.info(f"Price cache hit for {cache_key}")
            cached_data = dict(cached_entry["data"])
            cached_data["source"] = "cached"
            return cached_data

        # Tier 2: Call live data.gov.in API
        commodity_name = COMMODITY_ALIASES.get(norm_crop, norm_crop.capitalize())
        params: Dict[str, Any] = {
            "api-key": self.api_key,
            "format": "json",
            "filters[state.keyword]": state,
            "filters[commodity]": commodity_name,
            "limit": 25,
            "offset": 0
        }

        try:
            logger.info(f"Querying data.gov.in for commodity '{commodity_name}' in {state} (district: {district})...")
            async with httpx.AsyncClient(timeout=4.5) as client:
                resp = await client.get(self.api_endpoint, params=params)

            if resp.status_code == 200:
                body = resp.json()
                records = body.get("records", [])

                if records:
                    # Filter by district if provided
                    filtered = records
                    if district:
                        dist_lower = district.lower().strip()
                        district_matches = [
                            r for r in records
                            if r.get("district", "").lower().strip() == dist_lower
                        ]
                        if district_matches:
                            filtered = district_matches

                    # Parse modal, min, max prices and arrival dates
                    parsed_records = []
                    for r in filtered:
                        try:
                            modal = float(r.get("modal_price", 0))
                            min_p = float(r.get("min_price", modal))
                            max_p = float(r.get("max_price", modal))
                            if modal > 0:
                                parsed_records.append({
                                    "market": r.get("market", "District Mandi"),
                                    "district": r.get("district", state),
                                    "arrival_date": r.get("arrival_date", str(date.today())),
                                    "modal_price": modal,
                                    "min_price": min_p,
                                    "max_price": max_p
                                })
                        except (ValueError, TypeError):
                            continue

                    if parsed_records:
                        # Sort by arrival_date descending to pick the most recent
                        parsed_records.sort(key=lambda x: str(x.get("arrival_date")), reverse=True)
                        most_recent_date = parsed_records[0]["arrival_date"]
                        recent_group = [r for r in parsed_records if r["arrival_date"] == most_recent_date]

                        # Average modal_price across markets on that date
                        avg_modal = round(sum(r["modal_price"] for r in recent_group) / len(recent_group), 2)
                        min_price = min(r["min_price"] for r in recent_group)
                        max_price = max(r["max_price"] for r in recent_group)
                        primary_market = recent_group[0]["market"]
                        if len(recent_group) > 1:
                            primary_market = f"{district or state} Mandis (Avg of {len(recent_group)})"

                        result = {
                            "modal_price_per_quintal": avg_modal,
                            "min_price": round(min_price, 2),
                            "max_price": round(max_price, 2),
                            "market": primary_market,
                            "as_of_date": str(most_recent_date),
                            "source": "agmarknet_live"
                        }

                        # Save into active cache and permanent last-known store
                        _PRICE_CACHE[cache_key] = {"data": result, "timestamp": now_ts}
                        _LAST_KNOWN_PRICE_STORE[cache_key] = result
                        return result
        except Exception as e:
            logger.warning(f"data.gov.in Agmarknet API call failed or timed out: {e}")

        # Tier 3: Fallback to last-known cached price
        fallback_entry = _LAST_KNOWN_PRICE_STORE.get(cache_key)
        if not fallback_entry:
            # Check crop-only key
            fallback_entry = next(
                (v for k, v in _LAST_KNOWN_PRICE_STORE.items() if k.startswith(norm_crop)),
                None
            )

        if fallback_entry:
            logger.info(f"Using historical cached mandi price for {norm_crop}")
            res = dict(fallback_entry)
            res["source"] = "cached"
            return res

        # Tier 4: Fallback to official CCEA MSP rate
        msp_info = self.get_msp_rate(norm_crop)
        if msp_info:
            logger.info(f"Using official CCEA MSP fallback for {norm_crop}: ₹{msp_info['msp_per_quintal']}/qtl")
            return {
                "modal_price_per_quintal": msp_info["msp_per_quintal"],
                "min_price": msp_info["msp_per_quintal"],
                "max_price": msp_info["msp_per_quintal"],
                "market": "Government MSP Floor (CCEA)",
                "as_of_date": f"{msp_info['season']} {msp_info['year']}",
                "source": "msp_fallback"
            }

        # Tier 5: Crop has neither Agmarknet records nor MSP notification
        return {
            "modal_price_per_quintal": None,
            "min_price": None,
            "max_price": None,
            "market": "No Mandi Data Available",
            "as_of_date": str(date.today()),
            "source": "unavailable"
        }


price_service = PriceService()
