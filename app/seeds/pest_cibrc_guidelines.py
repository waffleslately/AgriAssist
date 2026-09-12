"""
Indian CIBRC (Central Insecticides Board & Registration Committee) and 
ICAR (Indian Council of Agricultural Research) Approved Integrated Pest Management (IPM) Matrix.
Includes DGCA-aligned Agricultural Drone Ultra-Low Volume (ULV) spraying parameters.
"""

PEST_CIBRC_GUIDELINES = {
    "cotton": {
        "pink_bollworm": {
            "name": "Pink Bollworm (गुलाबी सुंडी)",
            "scientific_name": "Pectinophora gossypiella",
            "etl": "8 moths/trap/night for 3 consecutive days OR 10% damaged rosette flowers or green bolls",
            "cultural_measures": [
                "Install Gossyplure pheromone traps @ 5 traps per acre for monitoring.",
                "Collect and destroy rosette flowers and dropped bolls."
            ],
            "biological_control": {
                "name": "Neem Oil / Azadirachtin 1500 ppm or Trichogramma bactrae",
                "dosage_per_acre": "1000 ml Neem oil (1500 ppm) OR 50,000 Trichogramma eggs/acre",
                "timing": "Initiate at first flower emergence"
            },
            "chemical_control": {
                "active_ingredient": "Emamectin Benzoate 5% SG or Chlorantraniliprole 18.5% SC",
                "trade_examples": "Proclaim / Coragen",
                "dosage_knapsack_per_acre": "88-100 g Emamectin Benzoate in 150-200 L water",
                "drone_dosage_per_acre": "88 g Emamectin Benzoate in 10 L water",
                "waiting_period_days": 14
            }
        },
        "whitefly": {
            "name": "Whitefly (सफेद मक्खी)",
            "scientific_name": "Bemisia tabaci",
            "etl": "6-8 nymphs/adults per leaf across top, middle, and lower canopies",
            "cultural_measures": [
                "Install yellow sticky traps @ 8 traps per acre.",
                "Avoid excessive nitrogenous fertilizer application."
            ],
            "biological_control": {
                "name": "Verticillium lecanii (Bio-pesticide)",
                "dosage_per_acre": "1000 g per acre in moist conditions",
                "timing": "Spray during early morning or late evening"
            },
            "chemical_control": {
                "active_ingredient": "Diafenthiuron 50% WP or Pyriproxyfen 10% EC",
                "trade_examples": "Pegasus / Lano",
                "dosage_knapsack_per_acre": "240 g Diafenthiuron in 150 L water",
                "drone_dosage_per_acre": "240 g Diafenthiuron in 10 L water",
                "waiting_period_days": 21
            }
        }
    },
    "maize": {
        "fall_armyworm": {
            "name": "Fall Armyworm (फॉल आर्मीवर्म)",
            "scientific_name": "Spodoptera frugiperda",
            "etl": "5% damaged plants at seedling stage; 10% whorl damage at mid-crop stage",
            "cultural_measures": [
                "Deep summer ploughing to expose pupae.",
                "Handpicking egg masses and early instars.",
                "Erect FAW-specific pheromone traps @ 5 traps per acre."
            ],
            "biological_control": {
                "name": "Bacillus thuringiensis (Bt) kurstaki or Metarhizium rileyi",
                "dosage_per_acre": "400 g Bt formulation per acre",
                "timing": "Apply at 1st-2nd instar larval stage"
            },
            "chemical_control": {
                "active_ingredient": "Chlorantraniliprole 18.5% SC or Spinetoram 11.7% SC",
                "trade_examples": "Coragen / Delegate",
                "dosage_knapsack_per_acre": "80 ml Chlorantraniliprole in 150 L water (directed into whorls)",
                "drone_dosage_per_acre": "80 ml Chlorantraniliprole in 10 L water",
                "waiting_period_days": 14
            }
        }
    },
    "paddy": {
        "yellow_stem_borer": {
            "name": "Yellow Stem Borer (तना छेदक)",
            "scientific_name": "Scirpophaga incertulas",
            "etl": "1 egg mass/sq.m or 5% dead hearts at vegetative stage or 2% white ears at flowering",
            "cultural_measures": [
                "Install pheromone traps @ 8 traps per acre.",
                "Clip seedling leaf tips before transplanting to eliminate egg masses."
            ],
            "biological_control": {
                "name": "Trichogramma japonicum",
                "dosage_per_acre": "40,000 parasitoids/acre released weekly",
                "timing": "At first sighting of moths"
            },
            "chemical_control": {
                "active_ingredient": "Chlorantraniliprole 0.4% GR or Cartap Hydrochloride 50% SP",
                "trade_examples": "Ferterra / Padan",
                "dosage_knapsack_per_acre": "4 kg Ferterra (granular broadcast) OR 400 g Cartap SP in 150 L water",
                "drone_dosage_per_acre": "400 g Cartap Hydrochloride 50% SP in 10 L water",
                "waiting_period_days": 21
            }
        },
        "blast": {
            "name": "Rice Blast (झुलसा रोग)",
            "scientific_name": "Magnaporthe oryzae",
            "etl": "Spindle-shaped lesions with ash-colored centers covering 2-5% leaf area",
            "cultural_measures": [
                "Avoid split excess application of urea nitrogen during cloudy weather.",
                "Ensure proper field drainage."
            ],
            "biological_control": {
                "name": "Pseudomonas fluorescens",
                "dosage_per_acre": "1000 g per acre as foliar spray",
                "timing": "Preventative spray at tillering"
            },
            "chemical_control": {
                "active_ingredient": "Tricyclazole 75% WP or Azoxystrobin 18.2% + Difenoconazole 11.4% SC",
                "trade_examples": "Beam / Amistar Top",
                "dosage_knapsack_per_acre": "120-160 g Tricyclazole in 150 L water",
                "drone_dosage_per_acre": "140 g Tricyclazole 75% WP in 10 L water",
                "waiting_period_days": 30
            }
        }
    },
    "wheat": {
        "yellow_rust": {
            "name": "Yellow / Stripe Rust (पीला रतुआ)",
            "scientific_name": "Puccinia striiformis",
            "etl": "Initial appearance of yellow pustules arranged in linear stripes on leaves",
            "cultural_measures": [
                "Regular field scouting during cool, humid periods in Jan-Feb.",
                "Grow rust-resistant varieties (e.g. HD-2967, PBW-550)."
            ],
            "biological_control": {
                "name": "Trichoderma viride",
                "dosage_per_acre": "1 kg/acre preventative",
                "timing": "Early vegetative stage"
            },
            "chemical_control": {
                "active_ingredient": "Propiconazole 25% EC",
                "trade_examples": "Tilt / Result",
                "dosage_knapsack_per_acre": "200 ml in 200 L water",
                "drone_dosage_per_acre": "200 ml Propiconazole 25% EC in 10 L water",
                "waiting_period_days": 30
            }
        }
    }
}

# Standard DGCA India Agricultural Drone Spraying Parameters
DGCA_DRONE_SPRAY_SOP = {
    "water_volume_litres_per_acre": 10.0,
    "flight_altitude_meters_above_canopy": 1.8,
    "flight_speed_m_per_s": 3.5,
    "swath_width_meters": 3.5,
    "droplet_size_microns": "150-250 (Anti-drift hollow cone / centrifugal nozzle)",
    "weather_constraints": {
        "max_wind_speed_kmh": 12.0,
        "max_temperature_celsius": 35.0,
        "no_rain_forecast_hours": 6
    }
}
