import asyncio
import json
import os
import sys
import shutil

# Add the backend directory to sys.path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parser import ReportParser
from aggregator import Aggregator

async def test_full_week():
    # Always clear cache for testing to ensure a fresh scan
    shutil.rmtree("cache_test_weekly", ignore_errors=True)
    parser = ReportParser(cache_dir="cache_test_weekly")
    aggregator = Aggregator()
    
    sample_pdf = r"d:\maks_ahp\MAKINDU AHP DAILY PROGRESS REPORT Saturday 18th April 2026.pdf"
    
    print("--- STEP 1: PARSING SAMPLE PDF ---")
    session_dir = "test_session_weekly"
    daily_data = await parser.parse_report(sample_pdf, session_dir, "DAILY")
    
    # Simulate a full week using this data
    print("--- STEP 2: SIMULATING 7 DAYS ---")
    seven_days = [daily_data for _ in range(7)]
    
    print("--- STEP 3: AGGREGATING ---")
    weekly_summary = aggregator.compile_weekly_data(seven_days)
    
    # Save the compiled weekly summary to a JSON file
    import os
    output_dir = os.path.join(os.path.dirname(__file__), "tests_output")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "WEEKLY_SUMMARY_RESULTS.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(weekly_summary, f, indent=2, ensure_ascii=False)
    print(f"📄 Weekly JSON saved to: {output_file}")
    
    print("\n--- WEEKLY LABOUR MATRIX (PREVIEW) ---")
    # Print the first 5 categories as a sample
    for cat, days in list(weekly_summary["labour"].items())[:5]:
        print(f"{cat:20}: {days}")
        
    print("\n--- WEEKLY WEATHER GRID ---")
    for w in weekly_summary["weather"]:
        print(f"{w['day']}: {w['morning']} | {w['afternoon']}")

    print("\n--- MATERIALS DELIVERED THIS WEEK ---")
    for name, data in list(weekly_summary["materials_sum"].items())[:5]:
        print(f"- {name}: {data['qty']} {data.get('unit', '')}")

if __name__ == "__main__":
    asyncio.run(test_full_week())
