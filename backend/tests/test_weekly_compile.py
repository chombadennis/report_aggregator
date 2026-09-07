import json
import os
import sys

# Ensure we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from generator import ReportGenerator

def run_test():
    # Mock data mirroring the form input
    data = {
        "title": "WEEK 41 PROGRESS REPORT",
        "report_date": "31ST AUGUST - 6TH SEPTEMBER, 2026",
        "time_elapsed": "41 Weeks",
        "pct_period": "39.32%",
        "pct_work": "13.90%"
    }
    
    template_path = "backend/weekly_template.docx"
    output_path = "backend/TEST_WEEK41_REPORT.docx"
    
    generator = ReportGenerator(template_path)
    generator.generate_report(output_path, data)
    
    print("Report generated successfully.")
    print(f"Check the output at {output_path}")
    
if __name__ == "__main__":
    run_test()
