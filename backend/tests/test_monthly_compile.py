import os
import sys

# Ensure we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from monthly_generator import MonthlyReportGenerator

def run_test():
    # Mock data mirroring the form input
    data = {
        "title": "MONTHLY REPORT (AUGUST 2026)",
        "report_date": "AUGUST 2026",
        "time_elapsed": "39 Weeks",
        "pct_period": "38.63%",
        "pct_work": "13.90%",
        "visitors": [
            {"name": "John Doe", "org": "NHA", "date": "12-08-2026"},
            {"name": "Jane Smith", "org": "Consulting Inc", "date": "15-08-2026"}
        ]
    }
    
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "monthly_report_template.docx")
    output_path = os.path.join(os.path.dirname(__file__), "tests_output", "TEST_MONTHLY_REPORT.docx")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    generator = MonthlyReportGenerator(template_path)
    generator.generate_report(output_path, data)
    
    print("Report generated successfully.")
    print(f"Check the output at {output_path}")
    print("Verify that Visitors Table is present and Cubes Table is untouched.")
    
if __name__ == "__main__":
    run_test()
