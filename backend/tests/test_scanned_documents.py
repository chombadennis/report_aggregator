import asyncio
import json
import os
import sys
import shutil

# Add the backend directory to sys.path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from document_parser import DocumentParser

async def test_scanned_file(parser: DocumentParser, pdf_path: str):
    print(f"\n=========================================")
    print(f"TESTING FILE: {os.path.basename(pdf_path)}")
    print(f"=========================================")
    
    if not os.path.exists(pdf_path):
        print(f"[ERROR] Scanned PDF not found at {pdf_path}!")
        return
        
    print("Initiating Multi-Page Scanned PDF Parse via Gemini Vision...")
    try:
        result = await parser.parse_document(pdf_path)
        
        print("\n--- RESULTS RECEIVED FROM GEMINI AI ---")
        print(f"Extracted Title: {result.get('title')}")
        print(f"Summary Brief: {result.get('summary')}")
        print("\nRequests Made by Contractor:")
        for idx, req in enumerate(result.get("requests_made", [])):
            print(f"  {idx+1}. {req}")
            
        print("\nAction Items:")
        for idx, item in enumerate(result.get("action_items", [])):
            print(f"  {idx+1}. {item}")
            
        print(f"\nContractual Implications & Risks:\n{result.get('contractual_implications')}")
        print(f"\nVerbatim Text/Visual Mode: {result.get('verbatim_text')}")
        print(f"Detailed Analysis Snippet: {str(result.get('detailed_analysis'))[:400]}...")
        
        # Verify multi-page and OCR extraction validity
        print("\n--- Validation Checklist ---")
        if result.get("title") and len(result.get("summary", "")) > 10:
            print("[PASS] Successful high-level document classification!")
        else:
            print("[FAIL] Missing or extremely sparse metadata analysis.")
            
        if len(result.get("requests_made", [])) > 0 or len(result.get("action_items", [])) > 0:
            print("[PASS] Successfully performed granular information extraction from pages!")
        else:
            print("[WARNING] No contractor requests or action items extracted. This is expected if the document is purely informational, but check if OCR was successful.")
            
    except Exception as e:
        print(f"[ERROR] Parsing failed with exception: {e}")

async def main():
    print("Starting Multi-Page Scanned Documents Visual OCR Test...")
    
    # Workspace root directory containing the scanned PDFs
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    
    pdf_paths = [
        os.path.join(workspace_root, "CONCRETE TEST RESULTS.pdf"),
        os.path.join(workspace_root, "February 2026 Site Meeting Minutes.pdf")
    ]
    
    # Use a clean test directory in cache so we do not overwrite active correspondence
    parser = DocumentParser(cache_dir="cache_test_scanned")
    
    try:
        for pdf_path in pdf_paths:
            await test_scanned_file(parser, pdf_path)
    finally:
        # Keep the cache folder so the user can inspect JSON outputs if desired, 
        # or clean it up if requested. We will clean it up to keep history clean.
        print("\nCleaning up temporary test cache...")
        if os.path.exists("cache_test_scanned"):
            shutil.rmtree("cache_test_scanned", ignore_errors=True)
            
    print("\n=== SCANNED DOCUMENTS MULTI-PAGE VISUAL OCR TEST COMPLETED ===")

if __name__ == "__main__":
    asyncio.run(main())
