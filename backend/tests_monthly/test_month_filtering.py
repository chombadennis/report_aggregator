import os
import sys

# Add the backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from monthly_aggregator import MonthlyAggregator

def test_month_filtering():
    aggregator = MonthlyAggregator(history_dir="history_monthly_test")
    
    # Test data: A week spanning March and April
    weekly_data = {
        "reporting_period": "30th March – 5th April 2026",
        "labour_daily": {
            "2026-03-30": {"Mason": "5"},
            "2026-03-31": {"Mason": "5"},
            "2026-04-01": {"Mason": "6"},
            "2026-04-02": {"Mason": "6"},
        },
        "weather_daily": {
            "2026-03-30": {"morning": "Rainy"},
            "2026-04-01": {"morning": "Sunny"},
        }
    }
    
    metadata = {"title": "MONTHLY REPORT (APRIL 2026)"}
    
    print("Testing aggregation for APRIL 2026...")
    result = aggregator.compile_monthly_data([weekly_data], metadata)
    
    # Check Labour: Should only have April 1 and 2
    # Monday is 30th March, Tuesday 31st, Wednesday 1st April, Thursday 2nd April.
    # index: Mon=0, Tue=1, Wed=2, Thu=3...
    labour_matrix = result["weekly_labour"][0]
    mason_values = labour_matrix.get("Mason", [])
    
    print(f"Mason values for the week: {mason_values}")
    assert mason_values[0] == "0" # Mon 30th March (Excluded)
    assert mason_values[1] == "0" # Tue 31st March (Excluded)
    assert mason_values[2] == "6" # Wed 1st April (Included)
    assert mason_values[3] == "6" # Thu 2nd April (Included)
    
    # Check Weather
    weather_grid = result["weekly_weather"][0]
    dates_included = [w["date_str"] for w in weather_grid]
    print(f"Dates included in weather: {dates_included}")
    assert "2026-03-30" not in dates_included
    assert "2026-04-01" in dates_included

    print("\n[OK] Month filtering test passed!")

if __name__ == "__main__":
    test_month_filtering()
