import asyncio
import json
import os
import sys
import shutil

# Add the backend directory to sys.path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from document_parser import DocumentParser

async def generate_mock_pdf(pdf_path: str):
    """Dynamically generates a mock construction EOT claim PDF using PyMuPDF."""
    print("Generating mock PDF claims document...")
    import fitz
    
    doc = fitz.open()
    page = doc.new_page()
    
    content = """MAKINDU AFFORDABLE HOUSING PROJECT
FORMAL CONTRACTOR CORRESPONDENCE

Date: 15th May 2026
Reference: MHP/EOT/003
To: The Project Manager, Makindu Housing Project Ltd
From: General Contractor Ltd

SUBJECT: FORMAL REQUEST FOR EXTENSION OF TIME (EOT) NO. 3 & ADDITIONAL DIRECT COSTS

Dear Sir,

We formally submit this request for an Extension of Time (EOT) of 14 calendar days under Clause 8.4 of the Contract Agreement, due to exceptional weather delays. 

From 10th May 2026 to 14th May 2026, the site experienced continuous torrential rainfall of over 75mm per day, causing severe flooding in Phase 1 foundation excavations and rendering site access roads completely impassable. 

Impact Details:
1. Phase 1 Foundations: Critical path works were completely halted for 5 days.
2. Labour Standby: 45 skilled masonry workers remained on standby.
3. Financial Claim: We also request the sum of KES 750,000 to cover direct overhead losses and standby plant rentals.

We request your urgent review, site instruction, and formal approval of this 14-day extension to update the Master Construction Schedule.

Yours faithfully,
Contractor Project Director
General Contractor Ltd
"""
    
    # Write the lines into the PDF
    y = 50
    for line in content.split('\n'):
        page.insert_text((50, y), line, fontsize=10)
        y += 15
        
    doc.save(pdf_path)
    doc.close()
    print(f"Mock PDF generated successfully at {pdf_path}")

async def run_tests():
    print("=== STARTING PROJECT CORRESPONDENCE & AI CLAIMS TEST ===")
    
    # 1. Create a test directory inside cache for temp tests
    test_pdf_path = "tests/test_claims_letter.pdf"
    await generate_mock_pdf(test_pdf_path)
    
    # 2. Instantiate DocumentParser
    print("\nInstantiating DocumentParser...")
    parser = DocumentParser(cache_dir="cache_test")
    
    try:
        # 3. Parse mock claims document
        print("\nSending mock claims document to Gemini for Structured analysis...")
        result = await parser.parse_document(test_pdf_path)
        
        print("\n[SUCCESS] AI CLAIMS ANALYSIS RESULT RECEIVED:")
        # Strip or replace unicode characters in result print if uvicorn logs them
        print(json.dumps(result, indent=2))
        
        # 4. Run assertions and print validations
        print("\n--- Running Logic and Integration Verifications ---")
        
        # Verify local PyMuPDF extraction
        verbatim = result.get("verbatim_text", "")
        if "EOT" in verbatim or "EOT" in result.get("title", ""):
            print("[PASS] Local PyMuPDF text reader successfully extracted claim content!")
        else:
            print("[FAIL] Local text extraction missing expected claim keywords.")
            
        # Verify AI extracted core fields
        if result.get("title"):
            print(f"[PASS] AI successfully identified Subject Title: '{result['title']}'")
        else:
            print("[FAIL] AI failed to extract title.")
            
        if len(result.get("requests_made", [])) > 0:
            print(f"[PASS] AI identified {len(result['requests_made'])} contractor request(s): {result['requests_made']}")
        else:
            print("[FAIL] AI did not extract any requests.")
            
        if len(result.get("action_items", [])) > 0:
            print(f"[PASS] AI identified {len(result['action_items'])} required action item(s): {result['action_items']}")
        else:
            print("[FAIL] AI did not extract any action items.")
            
        if result.get("contractual_implications"):
            print(f"[PASS] AI analyzed Contractual Implications/Risks: '{result['contractual_implications']}'")
        else:
            print("[FAIL] AI did not generate contractual implications.")
            
    except Exception as e:
        print(f"[ERROR] TEST FAILED with error: {e}")
        
    finally:
        # Cleanup mock files and test cache
        print("\nCleaning up test files and directories...")
        if os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)
        if os.path.exists("cache_test"):
            shutil.rmtree("cache_test", ignore_errors=True)
        print("=== TEST COMPLETED ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
