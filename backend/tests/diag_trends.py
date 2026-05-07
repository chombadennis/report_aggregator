import json
import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())

from analytics import AnalyticsEngine

def test_daily_trends():
    print("--- Testing Daily Trends Extraction ---")
    # Initialize engine with the actual paths used in main.py
    engine = AnalyticsEngine(history_dir="history", monthly_dir="cache/history_monthly")
    
    daily = engine.get_daily_trends()
    print(f"Total Daily Points: {len(daily)}")
    
    if daily:
        print("\nSample Data (First 3 days):")
        for d in daily[:3]:
            print(f"  {d['date']} | Labour: {d['labour']} | Materials: {d['materials']} | Disrupted: {d['weather_disrupted']}")
    else:
        print("ERROR: No daily data extracted!")
        
        # Debugging the directories
        print(f"\nChecking directories:")
        for dname in ["history", "cache/history_monthly"]:
            exists = os.path.exists(dname)
            if exists:
                files = os.listdir(dname)
                print(f"  - {dname}: EXISTS ({len(files)} files)")
            else:
                print(f"  - {dname}: MISSING")

    print("\n--- Correlation Debug ---")
    try:
        corr = engine.get_correlations()
        print(f"Correlation Matrix Keys: {list(corr.keys())}")
        if "scatter_labour_materials" in corr:
            print(f"Scatter Points: {len(corr['scatter_labour_materials'])}")
    except Exception as e:
        print(f"Correlation Error: {e}")

if __name__ == "__main__":
    test_daily_trends()
