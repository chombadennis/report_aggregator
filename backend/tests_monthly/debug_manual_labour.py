import fitz
import os
import json

def manual_extract_debug(pdf_path):
    doc = fitz.open(pdf_path)
    labour_data = {}
    materials_data = []
    days_of_week = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    
    last_labour_cat = None
    
    print(f"\n--- DEBUGGING PDF: {os.path.basename(pdf_path)} ---")
    
    for page_idx, page in enumerate(doc):
        tables = page.find_tables()
        for t_idx, table in enumerate(tables):
            raw_rows = table.extract()
            if not raw_rows: continue
            
            headers = [str(c).strip().upper() for c in raw_rows[0] if c]
            
            # --- 1. Labour Matrix Detection & Continuation ---
            is_labour = any("CATEGORY" in h for h in headers) and any(d in "".join(headers) for d in days_of_week)
            is_continuation = len(raw_rows[0]) == 8 and last_labour_cat is not None and not is_labour
            
            if is_labour or is_continuation:
                print(f"Found {'Labour' if is_labour else 'Continuation'} Table on Page {page_idx+1}, Table {t_idx+1}")
                day_indices = {i: i for i in range(1, 8)} # Default for headerless
                if is_labour:
                    day_indices = {}
                    for i, h in enumerate(headers):
                        for d_idx, d_name in enumerate(days_of_week):
                            if d_name in h: day_indices[d_idx] = i
                
                start_row = 1 if is_labour else 0
                for r_idx, row in enumerate(raw_rows[start_row:]):
                    if len(row) < 8: continue
                    cat = str(row[0] or "").strip()
                    
                    if not cat and last_labour_cat:
                        # Split row continuation
                        for d_idx in range(7):
                            col_idx = day_indices.get(d_idx+1 if is_continuation else d_idx)
                            if col_idx and col_idx < len(row):
                                val = str(row[col_idx] or "").strip()
                                if val:
                                    prev = labour_data[last_labour_cat][d_idx]
                                    labour_data[last_labour_cat][d_idx] = (prev + " " + val).strip()
                        continue

                    if not cat or cat.upper() in ["CATEGORY"]: continue
                    
                    last_labour_cat = cat
                    if cat not in labour_data:
                        labour_data[cat] = ["0"] * 7
                    
                    for d_idx in range(7):
                        col_idx = day_indices.get(d_idx+1 if is_continuation else d_idx)
                        if col_idx is not None and col_idx < len(row):
                            val = str(row[col_idx] or "").strip() or "0"
                            labour_data[cat][d_idx] = val
    return labour_data

if __name__ == "__main__":
    pdf_to_test = r"d:\maks_ahp\weeklies\MAKINDU AHP WEEKLY REPORT TEMPLATE FINAL 19TH WEEK MARCH AND APRIL.pdf"
    if os.path.exists(pdf_to_test):
        results = manual_extract_debug(pdf_to_test)
        print("\n--- FINAL MAPPED LABOUR DATA (WEEK 19) ---")
        print(json.dumps(results, indent=2))
    else:
        print(f"File not found: {pdf_to_test}")
