from parser import ReportParser
from aggregator import Aggregator
import json

def test_full_week():
    parser = ReportParser()
    aggregator = Aggregator()
    
    sample_pdf = r"d:\maks_ahp\MAKINDU AHP DAILY PROGRESS REPORT Saturday 18th April 2026.pdf"
    
    # 1. Parse one report
    daily_data = parser.parse_daily_report(sample_pdf)
    
    # 2. Simulate 7 days by duplicating it (just for the test)
    seven_days = [daily_data.copy() for _ in range(7)]
    
    # 3. Compile the week
    weekly_result = aggregator.compile_weekly_data(seven_days)
    
    # 4. Show a sample of the Labour Matrix and Weather Grid
    print("--- WEEKLY LABOUR MATRIX (SAMPLE) ---")
    # Show first 3 categories
    for cat in list(weekly_result["labour"].keys())[:5]:
        print(f"{cat}: {weekly_result['labour'][cat]}")
        
    print("\n--- WEEKLY WEATHER GRID ---")
    for day in weekly_result["weather"]:
        print(f"{day['day']}: {day['morning']} | {day['afternoon']}")

if __name__ == "__main__":
    test_full_week()
