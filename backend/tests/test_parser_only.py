import asyncio
import json
import os
import sys

# Add the backend directory to sys.path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parser import ReportParser

async def test_extraction():
    parser = ReportParser(cache_dir="cache_test")
    # PDF is in the project root, two levels up from backend
    sample_pdf = os.path.join("..", "..", "MAKINDU AHP DAILY PROGRESS REPORT Saturday 18th April 2026.pdf")
    session_dir = "test_session"
    
    print(f"🚀 Testing Parser extraction on: {sample_pdf}")
    
    # 1. Resumption check
    file_hash = parser._get_file_hash(sample_pdf)
    cache_path = os.path.join("cache_test", f"{file_hash}.json")
    if os.path.exists(cache_path):
        print(f"✅ Full cache found for {file_hash[:8]}. Using existing results.")
    else:
        print(f"🔄 Resuming or starting fresh scan for {file_hash[:8]}...")

    # 2. Run the Intelligent Scan
    try:
        data = await parser.parse_report(sample_pdf, session_dir)
        
        # 3. Save to a readable JSON file
        output_dir = os.path.join(os.path.dirname(__file__), "tests_output")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "PARSER_EXTRACTION_RESULTS.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ SUCCESS! Extraction complete.")
        print(f"📄 Results saved to: {output_file}")
        print("\n--- QUICK PREVIEW (Key Sections) ---")
        print(f"Date Found: {data.get('date')} ({data.get('day_of_week')})")
        print(f"Labour Count: {len(data.get('labour', {}))} categories")
        print(f"Weather: {data.get('weather')}")
        print(f"Instructions Found: {len(data.get('instructions', []))}")
        print(f"Interns: {data.get('interns')}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_extraction())
