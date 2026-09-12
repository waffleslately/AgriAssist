import io
import uuid
import requests
from PIL import Image

BASE_URL = "http://127.0.0.1:8000"

def test_full_pipeline():
    print("--- 1. Testing Scan Upload & Part A Response Schema ---")
    buf = io.BytesIO()
    img = Image.new("RGB", (640, 480), color=(60, 140, 70))
    img.save(buf, format="JPEG")
    buf.seek(0)

    test_plot_id = str(uuid.uuid4())
    files = {"file": ("drone_scan_latest.jpg", buf, "image/jpeg")}
    data = {
        "sensor_type": "rgb_vari",
        "crop_name": "wheat",
        "plot_id": test_plot_id,
        "plot_coordinates": '[[75.850, 30.900], [75.855, 30.900], [75.855, 30.905], [75.850, 30.905], [75.850, 30.900]]'
    }

    r = requests.post(f"{BASE_URL}/api/v1/drone/analyze-image", files=files, data=data, timeout=15)
    print(f"Analyze Status: {r.status_code}")
    assert r.status_code == 200, f"Expected 200, got: {r.text}"
    res = r.json()

    # Verify Part A deliverables
    assert "cells" in res, "Missing 'cells' in response"
    assert len(res["cells"]) > 0, "'cells' array is empty"
    first_cell = res["cells"][0]
    print(f"Sample Cell: {first_cell}")
    assert "x" in first_cell and "y" in first_cell, "Missing pixel x/y in cell"
    assert "norm_x" in first_cell and "norm_y" in first_cell, "Missing norm_x/norm_y in cell"
    assert "ndvi" in first_cell and "status" in first_cell, "Missing ndvi/status in cell"

    assert "weed_detections" in res, "Missing 'weed_detections' in response"
    assert "image_url" in res, "Missing 'image_url' in response"
    print(f"[PASS] Part A Response Schema verified! Scan ID: {res['scan_id']}, Image URL: {res['image_url']}\n")

    latest_scan_id = res["scan_id"]

    print("--- 2. Testing Seeding Historical Scans ---")
    r_seed = requests.post(f"{BASE_URL}/api/v1/drone/seed-demo-history/{test_plot_id}", timeout=10)
    print(f"Seed Status: {r_seed.status_code}, Body: {r_seed.json()}")
    assert r_seed.status_code == 200
    actual_plot_id = r_seed.json().get("plot_id", test_plot_id)

    print("\n--- 3. Testing GET /plots/{plot_id}/development-history (Part B) ---")
    r_hist = requests.get(f"{BASE_URL}/api/v1/plots/{actual_plot_id}/development-history", timeout=10)
    print(f"History Status: {r_hist.status_code}")
    assert r_hist.status_code == 200, f"History request failed: {r_hist.text}"
    hist = r_hist.json()
    print(f"History Response: {hist}")

    assert hist["plot_id"] == actual_plot_id
    assert "scans" in hist
    assert len(hist["scans"]) >= 3, f"Expected at least 3 scans, got {len(hist['scans'])}"

    for s in hist["scans"]:
        print(f" Scan Date: {s['scan_date']} | Avg NDVI: {s['avg_ndvi']} | Healthy: {s['healthy_pct']}% | Mod: {s['moderate_pct']}% | Stressed: {s['stressed_pct']}%")
        assert "scan_date" in s
        assert "avg_ndvi" in s
        assert "healthy_pct" in s
        assert "moderate_pct" in s
        assert "stressed_pct" in s

    print("[PASS] Part B Development History aggregated trend verified!\n")

    print("--- 4. Testing GET /api/v1/drone/scan-detail/{scan_id} (Swapping) ---")
    r_det = requests.get(f"{BASE_URL}/api/v1/drone/scan-detail/{latest_scan_id}", timeout=10)
    print(f"Detail Status: {r_det.status_code}")
    assert r_det.status_code == 200
    det = r_det.json()
    assert det["scan_id"] == latest_scan_id
    assert "grid" in det
    print("[PASS] Historical Scan Detail swapping endpoint verified!\n")

    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_full_pipeline()
