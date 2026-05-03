import fitz
import os

pdf_path = "MAKINDU AHP WEEK 19 PROGRESS REPORT.pdf"
if not os.path.exists(pdf_path):
    print(f"File {pdf_path} not found in root.")
else:
    doc = fitz.open(pdf_path)
    print(f"Total pages: {len(doc)}")
    for i in range(min(len(doc), 15)):
        print(f"\n--- PAGE {i+1} ---")
        print(doc[i].get_text())
