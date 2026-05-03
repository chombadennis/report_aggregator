import fitz
import os

pdf_path = r"d:\maks_ahp\MAKINDU AHP WEEKLY REPORT TEMPLATE FINAL 19TH WEEK MARCH AND APRIL.pdf"
doc = fitz.open(pdf_path)

for i in [4, 5, 6, 7]: # Pages 5, 6, 7, 8 (0-indexed 4, 5, 6, 7)
    print(f"\n--- Page {i+1} ---")
    text = doc[i].get_text()
    print(text)
