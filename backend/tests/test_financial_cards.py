import os
import json
import sys
from financial_engine import FinancialEngine

def test_financial_cards():
    print("Testing Financial Engine calculations for Revenue Accrued and Slippage Gap...")
    
    # Check if cache files exist
    if not os.path.exists("cache/history") and not os.path.exists("cache/history_monthly"):
        print("Warning: History directories not found. Financial calculations might be empty.")
    
    try:
        engine = FinancialEngine()
        financial_data = engine.compute_and_cache_financials()
        
        # Test Weekly Financials (which are likely used in the trends page for cards)
        weekly = financial_data.get("weekly_financials", [])
        if not weekly:
            print("No weekly financials generated!")
        else:
            latest_week = weekly[-1]
            print(f"\n--- Latest Week: {latest_week.get('label')} ---")
            print(f"Revenue Accrued: KES {latest_week.get('revenue_earned', 0):,.2f}")
            print(f"Slippage Gap: {latest_week.get('slippage_gap', 0):.2f}%")
            print(f"Pct Work: {latest_week.get('pct_work', 0)}%")
            print(f"Pct Time: {latest_week.get('pct_time', 0)}%")
            
            if latest_week.get('revenue_earned', 0) == 0:
                print("FAILED: Revenue Accrued is 0.")
            if latest_week.get('slippage_gap', 0) == 0:
                print("FAILED: Slippage Gap is 0.")
                
        # Test Monthly Financials
        monthly = financial_data.get("monthly_financials", [])
        if not monthly:
            print("No monthly financials generated!")
        else:
            latest_month = monthly[-1]
            print(f"\n--- Latest Month: {latest_month.get('month')} ---")
            print(f"Revenue Accrued: KES {latest_month.get('revenue_earned', 0):,.2f}")
            print(f"Slippage Gap: {latest_month.get('slippage_gap', 0):.2f}%")

    except Exception as e:
        print(f"Error running Financial Engine: {e}")

if __name__ == "__main__":
    test_financial_cards()
