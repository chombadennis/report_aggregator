import asyncio
import json
import os
import sys

# Add the backend directory to sys.path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from document_parser import DocumentParser

async def test_pow():
    print("=== STARTING PROGRAM OF WORKS (POW) SCHEDULE AUDIT ===")
    
    pow_path = r"e:\MyProjects\maks_ahp\POW-Proposed Makindu AHP..pdf"
    if not os.path.exists(pow_path):
        print(f"Error: Target POW file not found at {pow_path}")
        return
        
    print(f"Found Program of Works PDF at: {pow_path}")
    print("Parsing schedule and Gantt chart data using DocumentParser...")
    
    parser = DocumentParser(cache_dir="cache")
    
    try:
        # Run claims and schedule analysis
        result = await parser.parse_document(pow_path)
        
        print("\n[SUCCESS] SCHEDULING ANALYSIS COMPLETE!")
        print("\n--- AI EXTRACTED SCHEDULING PROFILE ---")
        print(f"Title: {result.get('title')}")
        print(f"Summary: {result.get('summary')}")
        
        print("\n--- CONTRACTUAL RISKS & SCHEDULE DELAY EVALUATION ---")
        print(result.get("contractual_implications"))
        
        print("\n--- EXTRACTED SCHEDULE DATES & KEY DEADLINES ---")
        print(result.get("detailed_analysis"))
        
        print("\n--- KEY ACTION ITEMS FOR PROJECT MANAGER ---")
        for idx, item in enumerate(result.get("action_items", [])):
            print(f"{idx+1}. {item}")
            
        print("\n--- DETECTED CRITICAL PATH REQUESTS ---")
        for idx, item in enumerate(result.get("requests_made", [])):
            print(f"{idx+1}. {item}")
            
    except Exception as e:
        print(f"[ERROR] Schedule parsing failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_pow())
