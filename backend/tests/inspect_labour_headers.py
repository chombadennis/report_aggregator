import docx

doc = docx.Document("weekly_template.docx")
for idx, table in enumerate(doc.tables):
    if table.rows:
        first_cell = table.rows[0].cells[0].text.strip().upper()
        if "CATEGORY" in first_cell:
            headers = [c.text.strip().replace('\n', ' ') for c in table.rows[0].cells]
            print(f"Table {idx} Headers: {headers}")
            print(f"Number of columns: {len(table.columns)}")
