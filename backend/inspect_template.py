from docx import Document
import fitz  # PyMuPDF
import os

def inspect_template(path):
    doc = Document(path)
    print(f"\n{'='*60}")
    print(f"TEMPLATE: {path}")
    print(f"Total Tables: {len(doc.tables)}")
    print(f"Total Paragraphs: {len(doc.paragraphs)}")
    print(f"{'='*60}\n")

    print("--- PARAGRAPHS WITH 'DATE' ---")
    for i, para in enumerate(doc.paragraphs):
        if "DATE" in para.text.upper() or "WEEK" in para.text.upper() or "PERIOD" in para.text.upper():
            print(f"  Para {i}: {para.text[:120]!r}")

    print("\n--- ALL TABLES (first 2 rows each) ---")
    for i, table in enumerate(doc.tables):
        print(f"\nTable {i} — {len(table.rows)} rows x {len(table.columns)} cols")
        for r_idx, row in enumerate(table.rows[:3]):
            cells = [c.text.strip()[:30] for c in row.cells]
            print(f"  Row {r_idx}: {cells}")

def inspect_pdf(path):
    print(f"\n{'='*60}")
    print(f"WEEKLY REPORT PDF: {path}")
    print(f"{'='*60}\n")
    doc = fitz.open(path)
    for i in range(min(5, len(doc))):  # First 5 pages only
        text = doc[i].get_text()
        print(f"\n--- Page {i+1} (first 800 chars) ---")
        print(text[:800])

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    inspect_template("weekly_template.docx")
    # Read the weekly PDF from d:\maks_ahp
    pdf_path = r"d:\maks_ahp\MAKINDU AHP WEEK 20 PROGRESS REPORT.pdf"
    if os.path.exists(pdf_path):
        inspect_pdf(pdf_path)
    else:
        print(f"PDF not found: {pdf_path}")
