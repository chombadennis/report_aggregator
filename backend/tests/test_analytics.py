import os
import sys
import json
import asyncio
from datetime import datetime

# Ensure UTF-8 output encoding for Windows command line compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add the parent directory to sys.path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics import AnalyticsEngine
from contract_parser import ContractParser

async def run_analytics_test():
    print("🚀 Starting Analytics Debug Test...")
    
    # Initialize Engine
    # Ensure we use the correct history directory relative to the backend folder
    history_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "history")
    engine = AnalyticsEngine(history_dir=history_dir)
    contract_parser = ContractParser()
    
    print(f"📂 Analyzing reports in: {history_dir}")
    
    # 1. Test Historical Trends Extraction
    print("\n--- 📊 PHASE 1: Quantitative Trends ---")
    trends = engine.get_historical_trends()
    
    if not trends:
        print("❌ No labour trends found. Check if history directory has JSON files.")
    else:
        for entry in trends:
            print(f"📅 Week: {entry['label']}")
            print(f"   👷 Avg Labour: {entry['value']}")
            print(f"   🚚 Materials: {entry['materials']}")
            print(f"   ☁️ Weather Disrupted: {entry['weather_disrupted']}")

    # 2. Test Risk Indicators
    has_warnings = False
    for entry in trends:
        if entry.get("warnings"):
            has_warnings = True
            for w in entry["warnings"]:
                print(f"⚠️ [Warning] {w} on {entry['label']}")
        if entry.get("instructions"):
            has_warnings = True
            for inst in entry["instructions"]:
                print(f"📋 [Instruction] {inst} on {entry['label']}")
    if not has_warnings:
        print("✅ No critical risks or warnings detected in trends.")

    # 3. Test AI Insights (Optional - set RUN_AI=True to execute)
    RUN_AI = True # Set to True to test Gemini integration
    if RUN_AI:
        print("\n--- 👔 PHASE 3: AI Executive Summary ---")
        contract = contract_parser.get_contract_summary() or {"project_title": "Test Project"}
        
        print("🤖 Calling Gemini for Strategic Analysis...")
        insights = await engine.generate_ai_insights(trends, contract)
        
        print("\n📝 EXECUTIVE SUMMARY:")
        print(insights.get("executive_summary", "No summary generated."))
        
        print("\n💡 STRATEGIC ADVICE:")
        print(insights.get("critical_advice", "No advice generated."))
        
        print(f"\n⚖️ CLAIM VERDICT: {insights.get('claim_verdict', 'Unknown')}")
    else:
        print("\n⏭️ Skipping AI Phase (RUN_AI=False)")

    # 4. Save Results
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests_output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "analytics_debug_result.json")
    
    debug_data = {
        "timestamp": datetime.now().isoformat(),
        "trends": trends,
        "insights": insights if RUN_AI else None
    }
    
    with open(output_path, "w") as f:
        json.dump(debug_data, f, indent=2)
    
    print(f"\n✅ Test Complete. Results saved to: {output_path}")

if __name__ == "__main__":
    asyncio.run(run_analytics_test())
