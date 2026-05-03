import fitz
import os

pdf_path = r"d:\maks_ahp\MAKINDU AHP WEEKLY REPORT TEMPLATE FINAL 19TH WEEK MARCH AND APRIL.pdf"
doc = fitz.open(pdf_path)

for i in range(len(doc)):
    print(f"--- Page {i+1} ---")
    text = doc[i].get_text()
    if "LABOUR" in text.upper():
        print(f"FOUND LABOUR ON PAGE {i+1}")
        print(text)
    if "SUMMARY OF WORKS DONE TO DATE" in text.upper():
        print(f"FOUND SUMMARY ON PAGE {i+1}")
        # print(text)
