from docx import Document
import os

def inspect_template(path):
    doc = Document(path)
    print(f"\n{'='*60}")
    print(f"TEMPLATE: {path}")
    print(f"Total Tables: {len(doc.tables)}")
    print(f"Total Paragraphs: {len(doc.paragraphs)}")
    print(f"{'='*60}\n")

    print("--- PARAGRAPHS WITH 'PROGRESS' OR 'REPORT' ---")
    for i, para in enumerate(doc.paragraphs):
        text = para.text.upper()
        if "PROGRESS" in text or "REPORT" in text:
            print(f"  Para {i}: {para.text[:120]!r}")

    print("\n--- ALL TABLES (first 3 rows each) ---")
    for i, table in enumerate(doc.tables):
        print(f"\nTable {i} — {len(table.rows)} rows x {len(table.columns)} cols")
        max_rows = len(table.rows) if i == 0 else 5
        for r_idx, row in enumerate(table.rows[:max_rows]):
            try:
                cells = [c.text.strip()[:50] for c in row.cells]
                print(f"  Row {r_idx}: {cells}")
            except:
                print(f"  Row {r_idx}: [Error reading cells]")

if __name__ == "__main__":
    inspect_template("weekly_template.docx")

