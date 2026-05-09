import asyncio
import os
import sys
import json

# Add the backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parser import ReportParser

async def test_extraction():
    # Configuration
    REPORTS_DIR = r"d:\maks_ahp\weeklies"
    # Pick a sample weekly report
    PDF_FILE = "MAKINDU AHP WEEK 21 PROGRESS REPORT.pdf"
    pdf_path = os.path.join(REPORTS_DIR, PDF_FILE)
    
    if not os.path.exists(pdf_path):
        # Fallback to check if it's in another location if needed, 
        # but the user's setup usually has it there.
        print(f"❌ File not found: {pdf_path}")
        return

    session_dir = "test_extraction_session"
    os.makedirs(session_dir, exist_ok=True)
    
    # Initialize parser with a fresh test cache to force AI scanning
    test_cache = "cache_v2_test"
    if os.path.exists(test_cache):
        import shutil
        shutil.rmtree(test_cache)
    os.makedirs(test_cache, exist_ok=True)
    
    parser = ReportParser(cache_dir=test_cache)
    
    print(f"Starting Extraction Test for: {PDF_FILE}")
    print(f"This will test the new logic for 'A. Contract Details' extraction.\n")
    
    try:
        result = await parser.parse_report(pdf_path, session_dir, "WEEKLY")
        
        # Save results to a file for the user to inspect
        output_file = "extraction_test_result.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
            
        print("\nEXTRACTION COMPLETE!")
        print(f"Results saved to: {os.path.abspath(output_file)}")
        
        print("\n--- VERIFYING NEW FIELDS ---")
        new_fields = ["time_lapsed_weeks", "pct_period_elapsed", "pct_work_done"]
        for field in new_fields:
            val = result.get(field)
            status = "FOUND" if val else "MISSING"
            print(f"{status} | {field}: {val}")
            
    except Exception as e:
        print(f"❌ Error during extraction: {e}")

if __name__ == "__main__":
    asyncio.run(test_extraction())
