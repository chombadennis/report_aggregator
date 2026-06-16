import sys
import os
import json

# Add backend dir to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analytics import AnalyticsEngine
from financial_engine import FinancialEngine
from progress_generator import ProgressReportGenerator

def main():
    print("Initializing engines...")
    analytics_engine = AnalyticsEngine(history_dir="cache/history", monthly_dir="cache/history_monthly")
    financial_engine = FinancialEngine()
    progress_generator = ProgressReportGenerator()

    print("Fetching trends...")
    trends = analytics_engine.get_historical_trends()
    print("Computing financials...")
    financials = financial_engine.compute_and_cache_financials()

    insights = None
    insights_path = "cache/ai_insights.json"
    if os.path.exists(insights_path):
        try:
            with open(insights_path, "r") as f:
                insights = json.load(f)
        except Exception as e:
            print(f"Error reading insights cache: {e}")
            
    if not insights:
        print("No AI insights found in cache. Using fallback/empty insights.")
        insights = {
            "swot": {
                "strengths": ["Strong site organization", "Consistent material delivery"],
                "weaknesses": ["Labor shortage in week 3", "Subcontractor delays"],
                "opportunities": ["Dry season ahead", "Parallel structural work"],
                "threats": ["Material cost escalation", "Impending rainy season"]
            },
            "recommendations": {
                "to_client": ["Approve variation order #2 promptly."],
                "to_contractor": ["Increase labor force by 15% to recover baseline S-curve."]
            },
            "executive_summary": "This is a test executive summary showing the progress of Makindu Affordable Housing Project.",
            "critical_advice": "Ensure safety protocols are met.",
            "claim_verdict": "Low"
        }

    output_dir = os.path.join("tests", "tests_output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "PROGRESS_TEST_REPORT.docx")

    print(f"Generating report to {output_path}...")
    progress_generator.generate_report(output_path, trends, insights, financials)
    print("Report generated successfully!")

if __name__ == "__main__":
    main()
