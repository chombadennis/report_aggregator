import asyncio
import json
import os
from aggregator import Aggregator

async def test():
    cache_dir = "report_aggregator/backend/cache"
    files = [f for f in os.listdir(cache_dir) if f.startswith("DAILY_")]
    daily_reports = []
    
    target_dates = ["31st August", "1st September", "2nd September", "3rd September", "4th September", "5th September", "6th September"]
    
    for f in files:
        with open(os.path.join(cache_dir, f), "r", encoding="utf-8") as fp:
            data = json.load(fp)
            date_str = data.get("date", "")
            if any(t.lower() in date_str.lower() for t in target_dates) and "2026" in date_str:
                daily_reports.append(data)
    
    # Sort them manually to make sure they are exactly 7
    # aggregator will handle chronological sorting internally but needs exactly 7
    print(f"Loaded {len(daily_reports)} reports.")
    for d in daily_reports:
        print(" -", d.get("date"))
        
    agg = Aggregator(history_dir="report_aggregator/backend/cache/history")
    
    try:
        result = await agg.compile_weekly_data(daily_reports)
        
        print("\nTOTAL ROW IN LABOUR MATRIX:")
        print(result["labour"]["TOTAL"])
        
        print("\nTOTAL ROW IN LABOUR DAILY (09-06):")
        for date, mapping in result["labour_daily"].items():
            if "09-06" in date:
                print(mapping["TOTAL"])
    except Exception as e:
        print(f"Aggregation failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
