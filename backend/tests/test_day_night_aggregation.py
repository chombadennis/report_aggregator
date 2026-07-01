import asyncio
import json
import os
import sys

# Add the backend directory to sys.path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aggregator import Aggregator
from generator import ReportGenerator

async def test_day_night_aggregation():
    print("--- STARTING DAY & NIGHT LABOUR AGGREGATION TEST ---")
    
    # 1. Load cached daily reports from May 18 - 24, 2026
    daily_cache_files = [
        "DAILY_7c43e0d01e46d19aab974365760fe9ce36fb86b30841d7bc6f56e60b37a05f8d.json",  # Mon May 18
        "DAILY_086f072b0f9b679db37a5ece5d811d9b8751c47fdf662543074b8883680ae1d5.json",  # Tue May 19
        "DAILY_2e61fd3c4e6ce2e36a2cfe18a6af7d50221f9d85d6cf02cb52ee703220dfca34.json",  # Wed May 20
        "DAILY_86ed22636cebe5ec5941f57013fe32118773e50709be08e1695710e1488b288e.json",  # Thu May 21 (Day & Night)
        "DAILY_142135fe778cb1d2574cfde97bc7e247c08192acdc61c56dcfb60e05f086ae3f.json",  # Fri May 22 (Day & Night)
        "DAILY_f1a13668a43b8219b6eadb34d0cd3b68b2f45681874488b910a2195fc289f857.json",  # Sat May 23
        "DAILY_b0d979de5fd00df0b09cf1898912cc380f927a348cd81433b890757c1a1975bb.json"   # Sun May 24
    ]
    
    daily_results = []
    for f in daily_cache_files:
        path = os.path.join("cache", f)
        if not os.path.exists(path):
            print(f"[ERROR] Cached file {path} not found!")
            return
        with open(path, "r") as json_file:
            daily_results.append(json.load(json_file))
            
    print(f"Loaded {len(daily_results)} daily reports from cache.")

    # 2. Compile using Aggregator
    aggregator = Aggregator()
    weekly_data = await aggregator.compile_weekly_data(daily_results)
    
    # Verify that weekly_data["labour"] contains the correct values
    print("\nVerifying compiled labour data:")
    mason_data = weekly_data["labour"].get("Mason")
    print(f"  Mason Weekly Array: {mason_data}")
    total_data = weekly_data["labour"].get("TOTAL")
    print(f"  TOTAL Weekly Array: {total_data}")
    
    # 3. Add weekly report metadata
    weekly_data.update({
        "title": "MAKINDU AHP WEEKLY PROGRESS REPORT",
        "time_elapsed": "25 Weeks",
        "pct_period": "23.84%",
        "pct_work": "8.60%",
        "report_date": "18th - 24th May 2026"
    })
    
    # Save the output compiled JSON so we can inspect it
    os.makedirs(os.path.join("tests", "tests_output"), exist_ok=True)
    compiled_json_path = os.path.join("tests", "tests_output", "DAY_NIGHT_TEST_DATA.json")
    with open(compiled_json_path, "w") as f:
        json.dump(weekly_data, f, indent=2)
    print(f"Saved compiled weekly data JSON to: {compiled_json_path}")

    # 4. Generate the document
    template_path = "weekly_template.docx"
    output_docx_path = os.path.join("tests", "tests_output", "DAY_NIGHT_TEST_REPORT.docx")
    generator = ReportGenerator(template_path)
    generator.generate_report(output_docx_path, weekly_data, "WEEKLY")
    print(f"Generated test weekly report docx at: {output_docx_path}")

    # 5. Read back the generated docx to verify table headers
    import docx
    doc = docx.Document(output_docx_path)
    labour_table = None
    for idx, table in enumerate(doc.tables):
        if table.rows:
            first_cell = table.rows[0].cells[0].text.strip().upper()
            if "CATEGORY" in first_cell:
                labour_table = table
                break
                
    if not labour_table:
        print("[FAIL] Labour table not found in output DOCX!")
        return

    headers = [c.text.strip().replace('\n', ' ') for c in labour_table.rows[0].cells]
    print(f"\nGenerated Table Headers: {headers}")
    print(f"Number of Columns: {len(headers)}")
    
    # Check headers matching expected columns
    expected_headers = [
        "CATEGORY", "Mon", "Tue", "Wed", 
        "Thur - Day", "Thur - Night", 
        "Fri - Day", "Fri - Night", 
        "Sat", "Sun"
    ]
    if headers == expected_headers:
        print("[PASS] Headers matched expected dynamic day/night format perfectly!")
    else:
        print(f"[FAIL] Headers did not match! Expected: {expected_headers}")
        
    # Check some content
    # Mason row values:
    # Mon: 2(m), Tue: 2(m), Wed: 8(m), Thur-Day: 10(m), Thur-Night: 3(m), Fri-Day: 9(m), Fri-Night: 3(m), Sat: 10(m), Sun: 1(m)
    expected_mason_row = [
        "Mason", "2(m)", "2(m)", "8(m)", "10(m)", "3(m)", "9(m)", "3(m)", "10(m)", "1(m)"
    ]
    mason_matched = False
    for row in labour_table.rows[1:]:
        row_vals = [c.text.strip() for c in row.cells]
        if row_vals[0] == "Mason":
            print(f"Found Mason row: {row_vals}")
            if row_vals == expected_mason_row:
                print("[PASS] Mason row values match daily reports perfectly!")
                mason_matched = True
            else:
                print(f"[FAIL] Mason row mismatch! Expected: {expected_mason_row}")
                
    if not mason_matched:
        print("[FAIL] Mason row check failed.")
        
    print("\n--- DAY & NIGHT LABOUR AGGREGATION TEST COMPLETED ---")

if __name__ == "__main__":
    asyncio.run(test_day_night_aggregation())
