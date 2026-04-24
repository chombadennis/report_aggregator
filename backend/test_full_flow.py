import asyncio
import os
from parser import ReportParser
from aggregator import Aggregator
from generator import ReportGenerator

async def main():
    # Paths
    sample_pdf = r"d:\maks_ahp\MAKINDU AHP DAILY PROGRESS REPORT Saturday 18th April 2026.pdf"
    template_path = "weekly_template.docx"
    output_path = "TEST_WEEKLY_REPORT.docx"
    session_dir = "full_flow_session"
    os.makedirs(session_dir, exist_ok=True)

    # 1. Initialize
    parser = ReportParser()
    aggregator = Aggregator()
    generator = ReportGenerator(template_path)

    # 2. Deep Scan the Daily Report
    print(f"Deep Scanning: {os.path.basename(sample_pdf)}...")
    # We use the new 'parse_report' method with Vision support
    daily_data = await parser.parse_report(sample_pdf, session_dir, "DAILY")

    # 3. Aggregate (Simulate 7 days using the same data for the test)
    print("Aggregating 7-day summary...")
    weekly_data = aggregator.compile_weekly_data([daily_data] * 7)
    
    # Add dummy cover page data
    weekly_data.update({
        "time_elapsed": "20 Weeks",
        "pct_elapsed": "19.43%",
        "pct_work": "7.29%",
        "report_date": "12th April 2026"
    })

    # 4. Generate the Word Document
    print(f"Injecting data into {template_path}...")
    generator.generate_report(output_path, weekly_data, "WEEKLY")

    print(f"\n🚀 SUCCESS! Open your report: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
