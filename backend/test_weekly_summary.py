import asyncio
import json
from parser import ReportParser
from aggregator import Aggregator

async def test_full_week():
    parser = ReportParser()
    aggregator = Aggregator()
    
    sample_pdf = r"d:\maks_ahp\MAKINDU AHP DAILY PROGRESS REPORT Saturday 18th April 2026.pdf"
    
    print("--- STEP 1: PARSING SAMPLE PDF ---")
    daily_data = await parser.parse_daily_report(sample_pdf)
    
    # Simulate a full week using this data
    print("--- STEP 2: SIMULATING 7 DAYS ---")
    seven_days = [daily_data for _ in range(7)]
    
    print("--- STEP 3: AGGREGATING ---")
    weekly_summary = aggregator.compile_weekly_data(seven_days)
    
    print("\n--- WEEKLY LABOUR MATRIX (PREVIEW) ---")
    # Print the first 5 categories as a sample
    for cat, days in list(weekly_summary["labour"].items())[:5]:
        print(f"{cat:20}: {days}")
        
    print("\n--- WEEKLY WEATHER GRID ---")
    for w in weekly_summary["weather"]:
        print(f"{w['day']}: {w['morning']} | {w['afternoon']}")

    print("\n--- MATERIALS DELIVERED THIS WEEK ---")
    for m in weekly_summary["materials"][:5]:
        print(f"- {m['item']}: {m['qty']}")

if __name__ == "__main__":
    asyncio.run(test_full_week())
