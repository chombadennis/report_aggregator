import os
import sys
import json

# Add parent directory to sys.path to import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from financial_engine import FinancialEngine

def test_financial_engine():
    print("Testing FinancialEngine computations...")
    try:
        engine = FinancialEngine(analysis_dir="analysis")
        data = engine.compute_and_cache_financials()
        
        print("\n--- Financial Engine Output ---")
        with open("analysis/financial_test_output.json", "w") as f:
            json.dump(data, f, indent=2)
        print("Test output saved to analysis/financial_test_output.json")
        
    except Exception as e:
        import traceback
        print("\n❌ Error during computation:")
        traceback.print_exc()

if __name__ == "__main__":
    test_financial_engine()
