"""
ICAR (Indian Council of Agricultural Research) Fertilizer Guidelines
Nutrient values in kg per acre. Commercial bags:
- Urea: 45 kg bag (46% N)
- DAP: 50 kg bag (18% N, 46% P2O5)
- MOP: 50 kg bag (60% K2O)
- SSP: 50 kg bag (16% P2O5)
"""

CROP_GUIDELINES = {
    "wheat": {
        "name": "Wheat (गेंहू)",
        "season": "rabi",
        "rdf_kg_per_acre": {"N": 48.0, "P": 24.0, "K": 16.0},
        "growth_stages": [
            {"stage": "Basal (Sowing)", "min_das": 0, "max_das": 15, "n_pct": 50, "p_pct": 100, "k_pct": 100, "name_hi": "बुवाई का समय"},
            {"stage": "Crown Root Initiation (CRI)", "min_das": 16, "max_das": 35, "n_pct": 25, "p_pct": 0, "k_pct": 0, "name_hi": "जड़ विकास (CRI)"},
            {"stage": "Jointing / Flowering", "min_das": 36, "max_das": 65, "n_pct": 25, "p_pct": 0, "k_pct": 0, "name_hi": "गांठ बनने की अवस्था"},
            {"stage": "Grain Filling", "min_das": 66, "max_das": 120, "n_pct": 0, "p_pct": 0, "k_pct": 0, "name_hi": "दाना भरने की अवस्था"}
        ]
    },
    "paddy": {
        "name": "Paddy / Rice (धान)",
        "season": "kharif",
        "rdf_kg_per_acre": {"N": 50.0, "P": 25.0, "K": 20.0},
        "growth_stages": [
            {"stage": "Basal (Transplanting)", "min_das": 0, "max_das": 15, "n_pct": 50, "p_pct": 100, "k_pct": 100, "name_hi": "रोपाई का समय"},
            {"stage": "Active Tillering", "min_das": 16, "max_das": 35, "n_pct": 25, "p_pct": 0, "k_pct": 0, "name_hi": "कल्ले फूटने की अवस्था"},
            {"stage": "Panicle Initiation", "min_das": 36, "max_das": 60, "n_pct": 25, "p_pct": 0, "k_pct": 0, "name_hi": "बाली निकलने की शुरुआत"},
            {"stage": "Maturity", "min_das": 61, "max_das": 130, "n_pct": 0, "p_pct": 0, "k_pct": 0, "name_hi": "पकने की अवस्था"}
        ]
    },
    "cotton": {
        "name": "Cotton (कपास)",
        "season": "kharif",
        "rdf_kg_per_acre": {"N": 45.0, "P": 24.0, "K": 24.0},
        "growth_stages": [
            {"stage": "Basal (Sowing)", "min_das": 0, "max_das": 20, "n_pct": 33, "p_pct": 100, "k_pct": 50, "name_hi": "बुवाई का समय"},
            {"stage": "Square Formation", "min_das": 21, "max_das": 50, "n_pct": 33, "p_pct": 0, "k_pct": 50, "name_hi": "कलियां बनने की अवस्था"},
            {"stage": "Flowering & Boll Development", "min_das": 51, "max_das": 90, "n_pct": 34, "p_pct": 0, "k_pct": 0, "name_hi": "फूल और टिंडे बनने की अवस्था"},
            {"stage": "Maturity", "min_das": 91, "max_das": 160, "n_pct": 0, "p_pct": 0, "k_pct": 0, "name_hi": "चुनाई की अवस्था"}
        ]
    },
    "soybean": {
        "name": "Soybean (सोयाबीन)",
        "season": "kharif",
        "rdf_kg_per_acre": {"N": 12.0, "P": 24.0, "K": 16.0},
        "growth_stages": [
            {"stage": "Basal (Sowing)", "min_das": 0, "max_das": 20, "n_pct": 100, "p_pct": 100, "k_pct": 100, "name_hi": "बुवाई का समय"},
            {"stage": "Vegetative & Flowering", "min_das": 21, "max_das": 50, "n_pct": 0, "p_pct": 0, "k_pct": 0, "name_hi": "फूल आने की अवस्था"},
            {"stage": "Pod Filling", "min_das": 51, "max_das": 95, "n_pct": 0, "p_pct": 0, "k_pct": 0, "name_hi": "फलियां भरने की अवस्था"}
        ]
    },
    "maize": {
        "name": "Maize (मक्का)",
        "season": "kharif",
        "rdf_kg_per_acre": {"N": 48.0, "P": 24.0, "K": 20.0},
        "growth_stages": [
            {"stage": "Basal (Sowing)", "min_das": 0, "max_das": 15, "n_pct": 33, "p_pct": 100, "k_pct": 100, "name_hi": "बुवाई का समय"},
            {"stage": "Knee-High Stage", "min_das": 16, "max_das": 35, "n_pct": 33, "p_pct": 0, "k_pct": 0, "name_hi": "घुटने तक बढ़ने की अवस्था"},
            {"stage": "Tasseling & Silking", "min_das": 36, "max_das": 65, "n_pct": 34, "p_pct": 0, "k_pct": 0, "name_hi": "मूंछें और भुट्टे निकलने की अवस्था"}
        ]
    },
    "sugarcane": {
        "name": "Sugarcane (गन्ना)",
        "season": "annual",
        "rdf_kg_per_acre": {"N": 60.0, "P": 30.0, "K": 30.0},
        "growth_stages": [
            {"stage": "Germination (Planting)", "min_das": 0, "max_das": 30, "n_pct": 20, "p_pct": 100, "k_pct": 50, "name_hi": "अंकुरण"},
            {"stage": "Tillering", "min_das": 31, "max_das": 90, "n_pct": 30, "p_pct": 0, "k_pct": 25, "name_hi": "कल्ले फूटने की अवस्था"},
            {"stage": "Grand Growth", "min_das": 91, "max_das": 210, "n_pct": 30, "p_pct": 0, "k_pct": 25, "name_hi": "तीव्र वृद्धि की अवस्था"},
            {"stage": "Ripening", "min_das": 211, "max_das": 365, "n_pct": 20, "p_pct": 0, "k_pct": 0, "name_hi": "पकने की अवस्था"}
        ]
    },
    "mustard": {
        "name": "Mustard (सरसों)",
        "season": "rabi",
        "rdf_kg_per_acre": {"N": 32.0, "P": 16.0, "K": 12.0},
        "growth_stages": [
            {"stage": "Basal (Sowing)", "min_das": 0, "max_das": 15, "n_pct": 50, "p_pct": 100, "k_pct": 100, "name_hi": "बुवाई का समय"},
            {"stage": "Vegetative Growth", "min_das": 16, "max_das": 35, "n_pct": 25, "p_pct": 0, "k_pct": 0, "name_hi": "वानस्पतिक वृद्धि"},
            {"stage": "Flowering (Silique)", "min_das": 36, "max_das": 70, "n_pct": 25, "p_pct": 0, "k_pct": 0, "name_hi": "फूल आने की अवस्था"},
            {"stage": "Seed Filling", "min_das": 71, "max_das": 110, "n_pct": 0, "p_pct": 0, "k_pct": 0, "name_hi": "बीज भरने की अवस्था"}
        ]
    },
    "gram": {
        "name": "Chickpea / Gram (चना)",
        "season": "rabi",
        "rdf_kg_per_acre": {"N": 8.0, "P": 20.0, "K": 10.0},
        "growth_stages": [
            {"stage": "Basal (Sowing)", "min_das": 0, "max_das": 20, "n_pct": 100, "p_pct": 100, "k_pct": 100, "name_hi": "बुवाई का समय"},
            {"stage": "Vegetative", "min_das": 21, "max_das": 55, "n_pct": 0, "p_pct": 0, "k_pct": 0, "name_hi": "वानस्पतिक"},
            {"stage": "Flowering & Pod Set", "min_das": 56, "max_das": 90, "n_pct": 0, "p_pct": 0, "k_pct": 0, "name_hi": "फूल और फली बनने की अवस्था"}
        ]
    },
    "sunflower": {
        "name": "Sunflower (सूरजमुखी)",
        "season": "kharif",
        "rdf_kg_per_acre": {"N": 32.0, "P": 24.0, "K": 20.0},
        "growth_stages": [
            {"stage": "Basal (Sowing)", "min_das": 0, "max_das": 15, "n_pct": 33, "p_pct": 100, "k_pct": 100, "name_hi": "बुवाई का समय"},
            {"stage": "Vegetative", "min_das": 16, "max_das": 35, "n_pct": 33, "p_pct": 0, "k_pct": 0, "name_hi": "वनस्पति अवस्था"},
            {"stage": "Flowering", "min_das": 36, "max_das": 65, "n_pct": 34, "p_pct": 0, "k_pct": 0, "name_hi": "फूल आने की अवस्था"},
            {"stage": "Seed Filling", "min_das": 66, "max_das": 100, "n_pct": 0, "p_pct": 0, "k_pct": 0, "name_hi": "बीज भरने की अवस्था"}
        ]
    }
}
