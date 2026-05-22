import os
import json
import logging
from analytics import AnalyticsEngine

# Set up logging to see the errors clearly
logging.basicConfig(level=logging.INFO)

def diag_dashboard_data():
    print("\n--- [SEARCH] TRENDS DIAGNOSTIC START ---")
    
    # 1. Initialize Engine
    try:
        engine = AnalyticsEngine(history_dir="cache/history", monthly_dir="cache/history_monthly")
        print("OK: AnalyticsEngine initialized.")
    except Exception as e:
        print(f"ERR: Initialization Failed: {e}")
        return

    # 2. Test Trend Fetch
    print("\nAttempting to fetch historical trends...")
    try:
        trends = engine.get_historical_trends(source="weekly")
        print(f"OK: Fetch successful! Found {len(trends)} trend points.")
        
        if len(trends) > 0:
            for t in trends:
                print(f"   DATA: Week: {t['label']}")
                print(f"         Labour Avg: {t['value']} | Materials: {t['materials']}")
                print(f"         Weather Disrupted: {t['weather_disrupted']}")
                print(f"         Weather Notes: {t.get('weather_comments')}")
                print(f"         Prose: {t.get('prose_summary')[:100]}...")
                print(f"         Financial: {t.get('financial_progress')} Progress")
                print(f"         Instructions: {t.get('instructions')}")
                print("-" * 50)
        else:
            print("WARN: No trend data found. Checking raw sources...")
            
    except Exception as e:
        print(f"ERR: CRITICAL ERROR in get_historical_trends: {e}")
        import traceback
        traceback.print_exc()

    # 3. Inspect Cache directly
    print("\nChecking raw cache folder for WEEKLY_*.json files...")
    cache_dir = "cache"
    if os.path.exists(cache_dir):
        files = [f for f in os.listdir(cache_dir) if f.startswith("WEEKLY_") and f.endswith(".json")]
        print(f"FOLDER: Found {len(files)} files in cache.")
        for f in files[:2]: # Show first 2
            path = os.path.join(cache_dir, f)
            with open(path, "r") as j:
                data = json.load(j)
                print(f"   FILE: {f}: Period='{data.get('reporting_period')}', HasLabour='{'labour_daily' in data}'")
    else:
        print("ERR: Cache folder missing!")

    print("\n--- DONE: DIAGNOSTIC COMPLETE ---")

if __name__ == "__main__":
    diag_dashboard_data()
