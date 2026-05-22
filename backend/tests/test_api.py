import asyncio
import json
import os
import sys

# Ensure UTF-8 output encoding for Windows command line compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add the backend directory to sys.path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_client import generate_structured_data, get_access_token

async def test_vertex_connection():
    print("=== VERTEX AI CONNECTION TEST ===")
    
    # 1. Check Token
    print("Checking Google Auth Token (using GOOGLE_CREDENTIALS_JSON)...")
    try:
        token, project_id = get_access_token(0)
        if token:
            print(f"[OK] Auth Token retrieved successfully!")
            print(f"     GCP Project ID: {project_id}")
            print(f"     Token Preview: {token[:15]}...")
        else:
            print("[ERROR] FAILED to retrieve Auth Token. Check your .env and GOOGLE_CREDENTIALS_JSON.")
            return
    except Exception as token_err:
        print(f"[ERROR] Exception during token retrieval: {token_err}")
        return

    # 2. Check simple extraction
    # Look for the PDF in potential workspace locations
    possible_paths = [
        r"e:\MyProjects\maks_ahp\dailies\MAKINDU AHP DAILY PROGRESS REPORT Saturday 18th April 2026.pdf",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dailies", "MAKINDU AHP DAILY PROGRESS REPORT Saturday 18th April 2026.pdf")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dailies", "MAKINDU AHP DAILY PROGRESS REPORT Saturday 18th April 2026.pdf")),
    ]
    
    sample_pdf = None
    for p in possible_paths:
        if os.path.exists(p):
            sample_pdf = p
            break
            
    if not sample_pdf:
        print(f"[ERROR] Sample PDF not found. Tried paths: {possible_paths}")
        return
        
    print(f"[OK] Found sample PDF at: {sample_pdf}")

    print(f"\nTesting AI Extraction with Vertex Flash...")
    prompt = "Identify the date of this report. Return ONLY a JSON like {'date': '...'}"
    
    try:
        result = await generate_structured_data(prompt, sample_pdf)
        print("[OK] Vertex AI Response Received!")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"[ERROR] Vertex AI Error during generation: {e}")

if __name__ == "__main__":
    asyncio.run(test_vertex_connection())
