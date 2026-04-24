import asyncio
import json
import os
from ai_client import generate_structured_data, get_access_token

async def test_vertex_connection():
    print("--- VERTEX AI CONNECTION TEST ---")
    
    # 1. Check Token
    print("Checking Google Auth Token...")
    token = get_access_token()
    if token:
        print(f"✅ Auth Token retrieved successfully: {token[:10]}...")
    else:
        print("❌ FAILED to retrieve Auth Token. Check your .env and GOOGLE_CREDENTIALS_JSON.")
        return

    # 2. Check simple extraction
    sample_pdf = r"d:\maks_ahp\MAKINDU AHP DAILY PROGRESS REPORT Saturday 18th April 2026.pdf"
    if not os.path.exists(sample_pdf):
        print(f"❌ Sample PDF not found at {sample_pdf}")
        return

    print(f"\nTesting AI Extraction with Vertex Flash...")
    prompt = "Identify the date of this report. Return ONLY a JSON like {'date': '...'}"
    
    try:
        result = await generate_structured_data(prompt, sample_pdf)
        print("✅ Vertex AI Response Received!")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Vertex AI Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_vertex_connection())
