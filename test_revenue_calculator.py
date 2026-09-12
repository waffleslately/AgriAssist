import requests
import json

BASE = "http://127.0.0.1:8000"

def test_revenue_calculator():
    # 1. Health check
    h = requests.get(f"{BASE}/health")
    assert h.status_code == 200, f"Health check failed: {h.status_code}"
    print("✓ Health check passed")

    # 2. Test Admin MSP Rates list
    r_msp = requests.get(f"{BASE}/api/v1/plots/admin/msp-rates")
    assert r_msp.status_code == 200, f"Admin MSP failed: {r_msp.status_code}"
    rates = r_msp.json().get("rates", {})
    assert "wheat" in rates
    assert "paddy" in rates
    assert "cotton" in rates
    print(f"✓ Seeded MSP Rates verified ({len(rates)} crops loaded). Wheat MSP: ₹{rates['wheat']['msp_per_quintal']}/qtl")

    # 3. Test Revenue Estimate (Default ICAR yield)
    sample_plot_id = "00000000-0000-0000-0000-000000000001"
    r_rev = requests.get(f"{BASE}/api/v1/plots/{sample_plot_id}/revenue-estimate")
    assert r_rev.status_code == 200, f"Revenue estimate failed: {r_rev.status_code} - {r_rev.text}"
    data = r_rev.json()
    print("\n=== REVENUE ESTIMATE (DEFAULT YIELD) ===")
    print(f"Crop: {data['crop_display']} ({data['crop_hi']})")
    print(f"Plot Area: {data['area_acres']} Acres")
    print(f"Expected Yield: {data['expected_yield_per_acre']} qtl/acre (ICAR default: {data['default_avg_yield_per_acre']})")
    print(f"Total Yield: {data['total_yield_quintals']} Quintals")
    print(f"Market Price: ₹{data['market_price']['modal_price_per_quintal']}/qtl (Source: {data['market_price']['source']}, Market: {data['market_price']['market']})")
    print(f"MSP Rate: ₹{data['msp_rate']['msp_per_quintal']}/qtl ({data['msp_rate']['season']} {data['msp_rate']['year']})")
    print(f"Revenue at Market Price: ₹{data['revenue_at_market_price']:,.2f}")
    print(f"Revenue at MSP: ₹{data['revenue_at_msp']:,.2f}")
    print(f"Estimated Revenue: ₹{data['estimated_revenue']:,.2f}")
    print(f"Better Option Note: {data['better_option_summary']}")
    print(f"Price Source Label: {data['price_source_label']}")

    assert data["estimated_revenue"] > 0
    assert data["total_yield_quintals"] > 0
    assert data["price_source_label"] is not None

    # 4. Test Revenue Estimate with Custom Yield slider value (e.g. 25.0 qtl/acre)
    r_rev_custom = requests.get(f"{BASE}/api/v1/plots/{sample_plot_id}/revenue-estimate?expected_yield_per_acre=25.0")
    assert r_rev_custom.status_code == 200
    custom_data = r_rev_custom.json()
    assert custom_data["expected_yield_per_acre"] == 25.0
    assert custom_data["total_yield_quintals"] == round(25.0 * custom_data["area_acres"], 2)
    assert custom_data["estimated_revenue"] > data["estimated_revenue"]
    print(f"\n✓ Custom Yield calculation verified: 25.0 qtl/acre -> ₹{custom_data['estimated_revenue']:,.2f}")

    # 5. Test direct alias route /plots/{plot_id}/revenue-estimate
    r_alias = requests.get(f"{BASE}/plots/{sample_plot_id}/revenue-estimate")
    assert r_alias.status_code == 200, f"Alias route failed: {r_alias.status_code}"
    print("✓ Direct alias route /plots/{plot_id}/revenue-estimate verified (200 OK)")

    # 6. Test Admin MSP Update
    update_payload = {
        "crop": "wheat",
        "msp_per_quintal": 2425.0,
        "season": "Rabi",
        "year": "2025-26"
    }
    r_up = requests.post(f"{BASE}/api/v1/plots/admin/msp-rates", json=update_payload)
    assert r_up.status_code == 200
    up_data = r_up.json()
    assert up_data["msp_record"]["msp_per_quintal"] == 2425.0
    print(f"✓ Admin MSP Update verified: Wheat MSP updated to ₹{up_data['msp_record']['msp_per_quintal']}/qtl")

    print("\nALL REVENUE CALCULATOR TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_revenue_calculator()
