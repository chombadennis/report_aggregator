import asyncio
import json
import os
from contract_parser import ContractParser

async def main():
    parser = ContractParser(cache_dir="cache")
    pdf_path = r"d:\maks_ahp\weeklies\MAKINDU AHP WEEK 20 PROGRESS REPORT.pdf"
    
    print(f"Extracting contract details from {pdf_path}...")
    result = await parser.extract_contract_details(pdf_path)
    
    if result:
        print("\n--- EXTRACTED CONTRACT SUMMARY ---")
        print(json.dumps(result, indent=2))
        print(f"\nSaved to {parser.contract_file}")
    else:
        print("Failed to extract details.")

if __name__ == "__main__":
    asyncio.run(main())
