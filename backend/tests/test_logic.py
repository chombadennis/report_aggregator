import asyncio
import json
import os
from parser import ReportParser
from aggregator import Aggregator
from dotenv import load_dotenv

load_dotenv()

async def main():
    pdf_path = r"e:/MyProjects/maks_ahp/dailies/MAKINDU AHP DAILY PROGRESS REPORT Friday 14th August 2026.pdf"
    
    print("1. Parsing Daily Report...")
    parser = ReportParser(cache_dir="cache")
    session_dir = "test_extraction_session"
    os.makedirs(session_dir, exist_ok=True)
    
    daily_data = await parser.parse_report(pdf_path, session_dir, report_type="DAILY")
    
    print("\n--- Extracted Daily JSON (Labour section) ---")
    print(json.dumps(daily_data.get("labour", {}), indent=2))
    
    print("\n2. Aggregating to Weekly Matrix...")
    aggregator = Aggregator(history_dir="history")
    
    try:
        weekly_data = await aggregator.compile_weekly_data([daily_data])
        print("\n--- Compiled Weekly Labour Matrix (Subset) ---")
        # Just print a few categories to keep it clean
        matrix = weekly_data.get("labour", {})
        for cat in ["Site Agent/PM", "Mason", "Unskilled", "Carpenters"]:
            if cat in matrix:
                print(f"{cat}: {matrix[cat]}")
        
    except Exception as e:
        print(f"Error compiling: {e}")

if __name__ == "__main__":
    asyncio.run(main())
