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
    
    print("--- STEP 1: PREPARING 7 UNIQUE PDF COPIES ---")
    # To test true parallel parsing without cache collisions, we need 7 unique files.
    # We will copy the sample PDF 7 times and append a tiny unique byte to change their hash.
    pdfs = []
    import tempfile
    for i in range(7):
        tmp_path = os.path.join(os.path.dirname(__file__), "tests_output", f"temp_day_{i}.pdf")
        shutil.copy(sample_pdf, tmp_path)
        with open(tmp_path, "ab") as f: f.write(f"{i}".encode())
        pdfs.append(tmp_path)
        
    print("--- STEP 2: PARSING ALL 7 DAYS IN PARALLEL (NO SEMAPHORE) ---")
    session_dir = "test_session_weekly"
    
    # Launch all 7 parsing tasks simultaneously
    tasks = [parser.parse_report(pdf, session_dir, "DAILY") for pdf in pdfs]
    daily_results = await asyncio.gather(*tasks)
    
    # Cleanup temp PDFs
    for pdf in pdfs:
        try: os.remove(pdf)
        except: pass

    # Simulate different days of the week so the aggregator fills the whole week
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for i, data in enumerate(daily_results):
        data["day_of_week"] = days[i]
        
    print("--- STEP 3: AGGREGATING 7 REPORTS INTO 1 WEEKLY SUMMARY (AI SEMANTIC DEDUPLICATION) ---")
    weekly_summary = await aggregator.compile_weekly_data(daily_results)
    
    # Save the compiled weekly summary to a JSON file
    output_dir = os.path.join(os.path.dirname(__file__), "tests_output")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "WEEKLY_SUMMARY_RESULTS.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(weekly_summary, f, indent=2, ensure_ascii=False)
    print(f"📄 Master Weekly JSON compiled from 7 parallel tasks saved to: {output_file}")
    
    print("\n--- WEEKLY LABOUR MATRIX (PREVIEW) ---")
    for cat, days in list(weekly_summary["labour"].items())[:5]:
        print(f"{cat:20}: {days}")
        
    print("\n--- WEEKLY WEATHER GRID ---")
    for w in weekly_summary["weather"]:
        print(f"{w['day']}: {w['morning']} | {w['afternoon']}")

    print("\n--- MATERIALS DELIVERED THIS WEEK ---")
    for name, data in list(weekly_summary.get("materials_sum", {}).items())[:5]:
        print(f"- {name}: {data.get('qty', 0)} {data.get('unit', '')}")

if __name__ == "__main__":
    asyncio.run(test_full_week())
