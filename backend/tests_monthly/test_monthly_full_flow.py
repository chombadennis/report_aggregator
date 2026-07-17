import asyncio
import os
import sys
import json

# Add the backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parser import ReportParser
from monthly_aggregator import MonthlyAggregator
from monthly_generator import MonthlyReportGenerator

async def main():
    # 1. SETUP PATHS
    root_dir = r"e:\MyProjects\maks_ahp\weeklies"
    weekly_pdfs = [
        os.path.join(root_dir, "MAKINDU AHP WEEK 28 PROGRESS REPORT.pdf"),
        os.path.join(root_dir, "MAKINDU AHP WEEK 29 PROGRESS REPORT.pdf"),
        os.path.join(root_dir, "MAKINDU AHP WEEK 30 PROGRESS REPORT.pdf"),
        os.path.join(root_dir, "MAKINDU AHP WEEK 31 PROGRESS REPORT.pdf"),
        os.path.join(root_dir, "MAKINDU AHP WEEK 32 PROGRESS REPORT.pdf")
    ]
    
    template_path = "monthly_report_template.docx"
    output_dir = os.path.join("tests_monthly", "monthly_test_outputs")
    json_dir = os.path.join(output_dir, "weekly_jsons")
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)
    
    output_docx = os.path.join(output_dir, "TEST_MONTHLY_REPORT.docx")
    final_json_path = os.path.join(output_dir, "monthly_data.json")
    session_dir = os.path.join(output_dir, "session")
    os.makedirs(session_dir, exist_ok=True)

    # 2. INITIALIZE
    parser = ReportParser(cache_dir="cache")
    aggregator = MonthlyAggregator(history_dir="cache/history_monthly")
    generator = MonthlyReportGenerator(template_path)

    # 3. PARSE WEEKLY REPORTS (Parallel - Limited to 2 at a time)
    print("\n--- Starting Parallel Parsing of Weekly Reports (Limit: 2) ---")
    semaphore = asyncio.Semaphore(2)
    
    async def parse_with_log(i, pdf_path):
        async with semaphore:
            print(f"Vision Scanning Week {i+28}: {os.path.basename(pdf_path)}...")
            data = await parser.parse_report(pdf_path, session_dir, "WEEKLY")
            
            # Save individual weekly JSON
            json_filename = f"week_{i+28}.json"
            json_path = os.path.join(json_dir, json_filename)
            with open(json_path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"✅ Saved weekly JSON: {json_path}")
            return data

    tasks = [parse_with_log(i, pdf_path) for i, pdf_path in enumerate(weekly_pdfs) if os.path.exists(pdf_path)]
    weekly_data_list = await asyncio.gather(*tasks)

    # 4. AGGREGATE
    print("\nAggregating monthly data (June 2026)...")
    # Metadata for June 2026
    metadata = {
        "title": "MONTHLY REPORT (JUNE 2026)",
        "report_date": "1ST – 30TH JUNE 2026",
        "time_elapsed": "30 Weeks",
        "pct_period": "28.84%",
        "pct_work": "11.22%"
    }
    
    monthly_summary = aggregator.compile_monthly_data(weekly_data_list, metadata)
    
    # Save final monthly JSON
    with open(final_json_path, "w") as f:
        json.dump(monthly_summary, f, indent=2)
    print(f"✅ Saved main monthly JSON: {final_json_path}")

    # 5. GENERATE WORD DOCUMENT
    print(f"Injecting data into {template_path}...")
    generator.generate_report(output_docx, monthly_summary)

    print(f"\n[OK] SUCCESS!")
    print(f"Monthly Docx: {output_docx}")
    print(f"Monthly JSON: {final_json_path}")
    print(f"Weekly JSONs: {json_dir}")

if __name__ == "__main__":
    asyncio.run(main())
