"""
IoT Livestock Grazing Simulator for AgriAssist Platform
Simulates GPS collars (Cattle, Buffalo, Sheep) grazing in a pasture field,
transmitting live coordinates and battery telemetry to the backend API.
"""

import time
import math
import random
import argparse
import requests

API_BASE = "http://127.0.0.1:8000/api/v1/iot"

ANIMALS = [
    {"tag_id": "COW-101", "type": "cattle", "battery": 96.0, "speed": 0.00008},
    {"tag_id": "COW-102", "type": "cattle", "battery": 91.5, "speed": 0.00006},
    {"tag_id": "COW-103", "type": "cattle", "battery": 98.2, "speed": 0.00009},
    {"tag_id": "BUF-201", "type": "buffalo", "battery": 82.0, "speed": 0.00004},
    {"tag_id": "SHP-301", "type": "sheep", "battery": 88.5, "speed": 0.00011},
]

def run_simulation(center_lat=30.9025, center_lng=75.8525, steps=30, interval=2.0):
    print(f"🚀 Starting IoT Livestock Grazing Telemetry Stream...")
    print(f"📍 Pasture Center: Lat {center_lat}, Lng {center_lng}")
    print(f"📡 Target Endpoint: {API_BASE}/telemetry")
    print(f"🐄 Simulating {len(ANIMALS)} GPS animal collars for {steps} cycles (interval: {interval}s)...\n")

    # Initial positions within a ~100m pasture box
    positions = {}
    for a in ANIMALS:
        positions[a["tag_id"]] = {
            "lat": center_lat + random.uniform(-0.0008, 0.0008),
            "lng": center_lng + random.uniform(-0.0008, 0.0008),
            "heading": random.uniform(0, 2 * math.pi)
        }

    for step in range(1, steps + 1):
        print(f"--- Cycle [{step}/{steps}] ---")
        for animal in ANIMALS:
            tag = animal["tag_id"]
            pos = positions[tag]

            # Wandering random walk model (grazing behavior)
            pos["heading"] += random.uniform(-0.6, 0.6)
            step_len = animal["speed"] * random.uniform(0.6, 1.4)
            pos["lat"] += step_len * math.cos(pos["heading"])
            pos["lng"] += step_len * math.sin(pos["heading"])

            # Soft boundary bouncing (keep within pasture radius ~150m)
            dist_from_center = math.hypot(pos["lat"] - center_lat, pos["lng"] - center_lng)
            if dist_from_center > 0.0016:
                # Steer back toward pasture center
                pos["heading"] = math.atan2(center_lng - pos["lng"], center_lat - pos["lat"])

            # Battery discharge
            animal["battery"] = max(10.0, round(animal["battery"] - random.uniform(0.01, 0.03), 1))

            payload = {
                "tag_id": tag,
                "animal_type": animal["type"],
                "latitude": round(pos["lat"], 6),
                "longitude": round(pos["lng"], 6),
                "battery_level": animal["battery"],
                "plot_id": "field_punjab_1"
            }

            try:
                r = requests.post(f"{API_BASE}/telemetry", json=payload, timeout=2.0)
                if r.status_code == 200:
                    print(f"  ✓ {tag} ({animal['type']}): Lat {payload['latitude']}, Lng {payload['longitude']} | Bat: {animal['battery']}%")
                else:
                    print(f"  ✗ {tag} Server Error {r.status_code}")
            except Exception as e:
                print(f"  ✗ {tag} Connection Failed: {e}")

        time.sleep(interval)

    print("\n✅ Simulation cycle completed! Check the map in AgriAssist to view the live herd and grazing heatmap.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate IoT GPS Collars for Livestock Grazing")
    parser.add_argument("--lat", type=float, default=30.9025, help="Pasture center latitude")
    parser.add_argument("--lng", type=float, default=75.8525, help="Pasture center longitude")
    parser.add_argument("--steps", type=int, default=15, help="Number of telemetry broadcast cycles")
    parser.add_argument("--interval", type=float, default=1.5, help="Seconds between cycles")
    args = parser.parse_args()

    run_simulation(center_lat=args.lat, center_lng=args.lng, steps=args.steps, interval=args.interval)
