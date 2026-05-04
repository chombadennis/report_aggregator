import fitz
import os

pdf_path = r"d:\maks_ahp\MAKINDU AHP WEEK 23 PROGRESS REPORT.pdf"
temp_repair = "repaired_test.pdf"

try:
    print("Repairing...")
    doc = fitz.open(pdf_path)
    doc.save(temp_repair, clean=True, deflate=True)
    doc.close()
    
    print("Reading Repaired...")
    doc2 = fitz.open(temp_repair)
    for i in range(15):
        text = doc2[i].get_text()
        print(f"Page {i+1} Length: {len(text)}")
        if len(text) > 0:
            print(f"Page {i+1} Text: {text[:100]}...")
    doc2.close()
except Exception as e:
    print(f"Error: {e}")
finally:
    if os.path.exists(temp_repair):
        os.remove(temp_repair)
