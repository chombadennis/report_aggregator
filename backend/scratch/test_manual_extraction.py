import sys
import os
import re
import fitz
import json

def manual_extract_daily_tables(doc):
    labour_data = {}
    materials_data = []
    
    for page in doc:
        tabs = page.find_tables()
        if not tabs:
            continue
            
        for tab in tabs:
            data = tab.extract()
            if not data or len(data) < 2:
                continue
                
            headers = [str(h).upper().strip() if h else "" for h in data[0]]
            
            # 1. LABOUR TURNOVER Identification
            if "CATEGORY" in headers and any("DAY" in h for h in headers):
                for row in data[1:]:
                    if not row or not row[0]: continue
                    cat = str(row[0]).strip()
                    if not cat: continue
                    
                    if len(row) == 2:
                        val = str(row[1]).strip() if row[1] else "0"
                    elif len(row) >= 3:
                        val_dict = {}
                        for i in range(1, len(row)):
                            h_name = headers[i] if i < len(headers) else f"Col_{i}"
                            h_norm = h_name.replace("NO.-", "").capitalize()
                            val_dict[h_norm] = str(row[i]).strip() if row[i] else "0"
                        val = val_dict
                    else:
                        val = "0"
                        
                    if "TOTAL" in cat.upper():
                        labour_data["TOTAL"] = val
                        break
                    labour_data[cat] = val

            # 2. MATERIALS DELIVERED TO SITE Identification
            if len(headers) == 3 and "DESCRIPTION" in headers and "QTY" in headers and "S/N" in headers:
                idx_desc = headers.index("DESCRIPTION")
                idx_qty = headers.index("QTY")
                
                for row in data[1:]:
                    if not row or len(row) <= max(idx_desc, idx_qty): continue
                    desc = str(row[idx_desc]).strip()
                    qty_full = str(row[idx_qty]).strip() if row[idx_qty] else "0"
                    if not desc or desc.upper() == "DESCRIPTION": continue
                    
                    qty_match = re.match(r'^(\d+\.?\d*)\s*(.*)$', qty_full)
                    if qty_match:
                        materials_data.append({
                            "description": desc,
                            "quantity": qty_match.group(1),
                            "units": qty_match.group(2).strip()
                        })
                    else:
                        materials_data.append({
                            "description": desc,
                            "quantity": qty_full,
                            "units": ""
                        })
    
    return labour_data, materials_data

doc_path = r'd:\maks_ahp\MAKINDU AHP DAILY PROGRESS REPORT Thursday 23rd April 2026.pdf'
doc = fitz.open(doc_path)
l, m = manual_extract_daily_tables(doc)

print("\n--- Manual Labour (JSON) ---")
print(json.dumps(l, indent=2))

print("\n--- Manual Materials (JSON) ---")
print(json.dumps(m, indent=2))
