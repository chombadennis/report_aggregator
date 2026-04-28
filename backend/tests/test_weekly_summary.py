import asyncio
import json
import os
import sys
import shutil

# Add the backend directory to sys.path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parser import ReportParser
from aggregator import Aggregator

# ── Real daily report PDFs (filenames contain the day, parser reads dates from cover page) ──
REPORTS_DIR = r"d:\maks_ahp"
DAILY_PDFS = [
    r"MAKINDU AHP DAILY PROGRESS REPORT Monday  13th April 2026-1.pdf",
    r"MAKINDU AHP DAILY PROGRESS REPORT Tuesday  14th April 2026-1.pdf",
    r"MAKINDU AHP DAILY PROGRESS REPORT Wednesday 15th April 2026.pdf",
    r"MAKINDU AHP DAILY PROGRESS REPORT Thursday 16th April 2026.pdf",
    r"MAKINDU AHP DAILY PROGRESS REPORT Friday 17th April 2026.pdf",
    r"MAKINDU AHP DAILY PROGRESS REPORT Saturday 18th April 2026.pdf",
    r"MAKINDU AHP DAILY PROGRESS REPORT Sunday 19th April 2026.pdf",
]

async def test_full_week():
    parser = ReportParser(cache_dir="cache_real_week")
    aggregator = Aggregator()

    # Build full paths
    pdfs = [os.path.join(REPORTS_DIR, f) for f in DAILY_PDFS]

    # Verify all files exist before starting
    missing = [p for p in pdfs if not os.path.exists(p)]
    if missing:
        print("❌ The following report files were not found:")
        for m in missing:
            print(f"   - {m}")
        return

    print(f"--- STEP 1: FOUND {len(pdfs)} DAILY REPORTS ---")
    for p in pdfs:
        print(f"   ✅ {os.path.basename(p)}")

    print("\n--- STEP 2: PARSING ALL 7 DAYS IN PARALLEL ---")
    session_dir = "session_real_week"

    # Launch all 7 parsing tasks simultaneously
    tasks = [parser.parse_report(pdf, session_dir, "DAILY") for pdf in pdfs]
    daily_results = await asyncio.gather(*tasks)

    print(f"\n--- STEP 3: AGGREGATING {len(daily_results)} REPORTS INTO WEEKLY SUMMARY ---")
    try:
        weekly_summary = await aggregator.compile_weekly_data(daily_results)
    except ValueError as e:
        # Date continuity check failed — stop and report to client
        print(f"\n{e}")
        return

    # Save the compiled weekly summary
    output_dir = os.path.join(os.path.dirname(__file__), "tests_output")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "WEEKLY_SUMMARY_RESULTS.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(weekly_summary, f, indent=2, ensure_ascii=False)
    print(f"📄 Master Weekly JSON saved to: {output_file}")

    print("\n--- WEEKLY LABOUR MATRIX (PREVIEW) ---")
    for cat, vals in weekly_summary["labour"].items():
        print(f"{cat:25}: {vals}")

    print("\n--- WEEKLY WEATHER GRID ---")
    for w in weekly_summary["weather"]:
        print(f"{w['day']}: {w['morning']} | {w['afternoon']}")

    print("\n--- MATERIALS DELIVERED THIS WEEK ---")
    for name, data in list(weekly_summary.get("materials_sum", {}).items())[:8]:
        print(f"  - {name}: {data.get('qty', 0)} {data.get('unit', '')}")

    print(f"\n--- CHALLENGES ---")
    print(weekly_summary.get("challenges", "None"))

if __name__ == "__main__":
    asyncio.run(test_full_week())
