import fitz
import json
import os

def test_specific_day():
    pdf_path = r"d:\maks_ahp\dailies\MAKINDU AHP DAILY PROGRESS REPORT Monday  13th April 2026-1.pdf"
    print(f"--- Manual Extraction for {os.path.basename(pdf_path)} ---")
    doc = fitz.open(pdf_path)
    
    labour = {}
    for page in doc:
        tables = page.find_tables()
        for table in tables:
            headers = [str(h).strip().upper() for h in table.header.names]
            if "CATEGORY" in headers:
                print(f"Found Labour table on page {page.number + 1}")
                data = table.extract()
                for row in data[1:]:
                    if len(row) >= 2:
                        cat = row[0].strip()
                        val = row[1].strip() or "0"
                        labour[cat] = val
    
    print("\n--- Extracted Labour ---")
    print(json.dumps(labour, indent=2))

if __name__ == "__main__":
    test_specific_day()
