from docx import Document

def inspect_template(path):
    doc = Document(path)
    print(f"Inspecting: {path}")
    print(f"Total Tables: {len(doc.tables)}")
    
    for i, table in enumerate(doc.tables):
        first_cell = table.cell(0, 0).text.strip() if table.rows else "Empty"
        print(f"Table {i}: First cell content: '{first_cell[:50]}'")

if __name__ == "__main__":
    inspect_template("weekly_template.docx")
