from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os
import copy
import re
from docx.shared import Inches, Pt

class MonthlyReportGenerator:
    def __init__(self, template_path):
        self.template_path = template_path

    def _find_table_by_header(self, doc, header_text):
        for table in doc.tables:
            if table.rows:
                for cell in table.rows[0].cells:
                    if header_text.upper() in cell.text.upper():
                        return table
        return None

    def _find_paragraph_anywhere(self, doc, text):
        """Searches for a paragraph containing specific text, even inside tables."""
        target = self._normalize_string(text)
        # Check top-level paragraphs
        for para in doc.paragraphs:
            if target in self._normalize_string(para.text):
                return para
        # Check inside tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        if target in self._normalize_string(para.text):
                            return para
        return None

    def _normalize_string(self, s: str):
        """Removes all non-alphanumeric characters and converts to uppercase for robust matching."""
        if not s: return ""
        return re.sub(r'[^A-Z0-9]', '', s.upper())

    def _insert_para_after(self, ref_element, text):
        """Inserts a new paragraph after the given element (can be a para or a table)."""
        new_p = OxmlElement('w:p')
        new_r = OxmlElement('w:r')
        new_t = OxmlElement('w:t')
        new_t.text = text
        new_t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        new_r.append(new_t)
        new_p.append(new_r)
        
        # Determine if we have a paragraph or an oxml element
        element = ref_element._p if hasattr(ref_element, '_p') else (ref_element._element if hasattr(ref_element, '_element') else ref_element)
        element.addnext(new_p)

    def generate_report(self, output_path, data):
        doc = Document(self.template_path)

        # 0. Page Setup (Preserve Template Settings)
        # We removed manual margin overrides to prevent footer repositioning

        # 1. Title (Cover Page)
        for para in doc.paragraphs:
            if "TITLE:" in para.text.upper() or "MONTHLY REPORT" in para.text.upper():
                val = data.get("title", "")
                if val:
                    para.text = ""
                    run = para.add_run(val)
                    run.bold = True
                    # If it's a cover page, maybe it should be larger
                    run.font.size = Pt(16)
                break

        # 2. Section A: Contract Details (Table 0)
        if doc.tables:
            table0 = doc.tables[0]
            mapping = {
                "time_elapsed": 13,     # Item 14
                "pct_period": 14,       # Item 15
                "pct_work": 15,         # Item 16
                "reporting_period": 16  # Item 17
            }
            for key, idx in mapping.items():
                if idx < len(table0.rows):
                    row = table0.rows[idx]
                    if len(row.cells) >= 3:
                        cell = row.cells[2]
                        val = str(data.get(key, ""))
                        cell.text = ""
                        run = cell.paragraphs[0].add_run(val)
                        run.bold = True

        # 3. Section D: Work Done Upto Date (Table 2)
        summary_table = self._find_table_by_header(doc, "SUMMARY OF WORK DONE TO DATE")
        if summary_table:
            summary_data = data.get("summary_to_date", {})
            for row in summary_table.rows[1:]:
                block = row.cells[0].text.strip().upper()
                if block in summary_data:
                    # Clear cell and add bulleted points
                    cell = row.cells[1]
                    cell.text = ""
                    raw_text = summary_data[block]
                    # Split by newline, semicolon, OR comma (since AI sometimes uses commas for lists)
                    points = [p.strip() for p in re.split(r'[\n;,]', raw_text) if p.strip()]
                    for p in points:
                        para = cell.add_paragraph()
                        para.text = f"• {p}"

        # 4. Section F: Cubes (Table 4) - Structural Overhaul
        cube_table = self._find_table_by_header(doc, "Compressive strength")
        if cube_table:
            # Shift all rows down by inserting a new header row at the top
            # We use OxmlElement directly to insert at the very beginning of the table
            new_tr = OxmlElement('w:tr')
            for i in range(len(cube_table.columns)):
                new_tc = OxmlElement('w:tc')
                new_p = OxmlElement('w:p')
                new_r = OxmlElement('w:r')
                new_t = OxmlElement('w:t')
                new_t.text = "Element." if i == 0 else ("Test." if i == 1 else "")
                new_r.append(new_t)
                new_p.append(new_r)
                new_tc.append(new_p)
                new_tr.append(new_tc)
            
            # Safely insert the new row before the first existing row to avoid corruption
            cube_table.rows[0]._element.addprevious(new_tr)
            # Make the new header bold
            for cell in cube_table.rows[0].cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.bold = True

        # 5. Section G: Machines (Table 5)
        machine_table = self._find_table_by_header(doc, "Condition")
        if machine_table:
            for row in machine_table.rows[1:]:
                name = row.cells[0].text.strip().upper()
                # Find in data
                match = next((m for m in data.get("machinery", []) if m["name"].upper() in name or name in m["name"].upper()), None)
                if match:
                    row.cells[1].text = match.get("qty", "1")
                    row.cells[2].text = match.get("condition", "Good")
                    row.cells[3].text = match.get("status", "Working")

        # 7. Section I: Materials (Dynamic Table Creation)
        active_mats = {k: v for k, v in data.get("materials_sum", {}).items() if v.get("qty", 0) > 0}
        if active_mats:
            target_para = self._find_paragraph_anywhere(doc, "MATERIALS DELIVERED")
            
            if target_para:
                # Create table after the paragraph
                new_tbl = doc.add_table(rows=1, cols=3)
                self._set_table_borders(new_tbl)
                # Set headers
                hdr_cells = new_tbl.rows[0].cells
                hdr_cells[0].text = 'S/NO.'
                hdr_cells[1].text = 'DESCRIPTION'
                hdr_cells[2].text = 'QUANTITY'
                for cell in hdr_cells:
                    for p in cell.paragraphs:
                        for run in p.runs:
                            run.bold = True
                
                # Fill data
                for i, (name, info) in enumerate(active_mats.items(), 1):
                    row = new_tbl.add_row()
                    row.cells[0].text = str(i)
                    row.cells[1].text = name
                    row.cells[2].text = f"{info['qty']} {info['unit']}"
                    # Ensure headers are bold (header is row 0)
                    for cell in new_tbl.rows[0].cells:
                        for p in cell.paragraphs:
                            for run in p.runs: run.bold = True
                
                # Move table to correct location (after target_para)
                target_para._p.addnext(new_tbl._tbl)

        # 8. Section H: Labour (Full Dynamic Table Creation)
        labour_header_para = self._find_paragraph_anywhere(doc, "LABOUR TURN OVER")
        
        # Also find the intro statement to ensure tables come AFTER it
        labour_intro = self._find_paragraph_anywhere(doc, "following were number of personnel")
        
        weekly_periods = data.get("weekly_periods", [])
        weekly_labour = data.get("weekly_labour", [])
        weekly_valid_days = data.get("weekly_valid_days", [[0,1,2,3,4,5,6]] * len(weekly_labour))
        
        days_header_map = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        
        # Target element for first insertion: Prefer the intro statement if found, else the header
        last_element = (labour_intro._p if labour_intro else labour_header_para._p) if (labour_intro or labour_header_para) else None

        for i, matrix in enumerate(weekly_labour):
            if not matrix: continue
            
            valid_days = weekly_valid_days[i]
            
            # 1. Create the Week Title Paragraph
            title_text = weekly_periods[i] if i < len(weekly_periods) else f"Week {i+1}"
            new_p = doc.add_paragraph(title_text)
            new_p.runs[0].bold = True
            
            # 2. Create the Table with dynamic columns
            categories = list(matrix.keys())
            if "TOTAL" in categories: 
                categories.remove("TOTAL")
                categories.sort()
                categories.append("TOTAL")
            else:
                categories.sort()
            
            # Category column + Valid days columns
            table = doc.add_table(rows=1, cols=len(valid_days) + 1)
            self._set_table_borders(table)
            hdr = table.rows[0].cells
            hdr[0].text = "CATEGORY"
            for col_idx, day_idx in enumerate(valid_days):
                hdr[col_idx + 1].text = days_header_map[day_idx]
            
            # Bold the headers
            for cell in hdr:
                for p in cell.paragraphs:
                    for run in p.runs: run.bold = True
            
            for cat in categories:
                row = table.add_row()
                row.cells[0].text = cat
                vals = matrix.get(cat, ["0"] * 7)
                for col_idx, day_idx in enumerate(valid_days):
                    row.cells[col_idx+1].text = str(vals[day_idx])
                
                # Bold the TOTAL row
                if cat.upper() == "TOTAL":
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            for run in p.runs:
                                run.bold = True
            
            # 3. Position them in the document
            if last_element is not None:
                last_element.addnext(new_p._p)
                new_p._p.addnext(table._element)
                # Update last_element to be the table we just added
                last_element = table._element

        # 9. Section J: Weather (Dynamic Table Creation)
        weather_header_para = self._find_paragraph_anywhere(doc, "WEATHER REPORT")
        weekly_weather = data.get("weekly_weather", [])
        
        # Insert after weather header
        last_weather_element = weather_header_para._p if weather_header_para else None

        for i, grid in enumerate(weekly_weather):
            if not grid: continue
            
            # 1. Week Title
            title_text = f"WEATHER REPORT: {weekly_periods[i]}"
            new_p = doc.add_paragraph(title_text)
            new_p.runs[0].bold = True
            
            # 2. Table
            table = doc.add_table(rows=1, cols=5)
            self._set_table_borders(table)
            hdr = table.rows[0].cells
            for idx, txt in enumerate(["DAY", "MORNING", "AFTERNOON", "EVENING", "CONDITION"]):
                hdr[idx].text = txt
                for p in hdr[idx].paragraphs:
                    for run in p.runs: run.bold = True
            
            for day_info in grid:
                row = table.add_row()
                row.cells[0].text = day_info.get("day", "")
                row.cells[1].text = day_info.get("morning", "-")
                row.cells[2].text = day_info.get("afternoon", "-")
                row.cells[3].text = day_info.get("evening", "-")
                row.cells[4].text = day_info.get("condition", "-")

            if last_weather_element is not None:
                last_weather_element.addnext(new_p._p)
                new_p._p.addnext(table._element)
                last_weather_element = table._element

                # Append Weather Comments
                comments = data.get("weather_comments", [])
                if i < len(comments) and comments[i] and comments[i].lower() != "none":
                    comment_points = [p.strip().lstrip('•').strip() for p in comments[i].split('\n') if p.strip()]
                    if comment_points:
                        # Comments label
                        comm_label = doc.add_paragraph("Comments:")
                        comm_label.runs[0].bold = True
                        table._element.addnext(comm_label._p)
                        last_weather_element = comm_label._p
                        for cp in comment_points:
                            cp_para = doc.add_paragraph(f"• {cp}")
                            last_weather_element.addnext(cp_para._p)
                            last_weather_element = cp_para._p

        # 9. Prose sections (H&S, Security, Challenges)
        section_map = [
            ("HEALTH AND SAFETY", data.get("health_safety", "")),
            ("SECURITY", data.get("security", "")),
            ("CHALLENGES", data.get("challenges", ""))
        ]
        for header, content in section_map:
            for para in doc.paragraphs:
                if header in para.text.upper() and len(para.text) < 40:
                    if content and content.lower() != "none":
                        # Split by existing bullets or newlines
                        points = [p.strip().lstrip('•').strip() for p in content.split('\n') if p.strip()]
                        # Insert in reverse order to maintain sequence with addnext
                        for p in reversed(points):
                            self._insert_para_after(para._p, f"• {p}")
                    break

        # 11. Site Instructions (Dynamic Table Creation)
        inst_header_para = self._find_paragraph_anywhere(doc, "SITE INSTRUCTIONS")
        inst_data = data.get("instructions", [])
        
        if inst_header_para and inst_data:
            # Create Table
            table = doc.add_table(rows=1, cols=4)
            self._set_table_borders(table)
            hdr = table.rows[0].cells
            for idx, txt in enumerate(["REF NO", "DETAILS", "DATE", "INSTRUCTOR"]):
                hdr[idx].text = txt
                for p in hdr[idx].paragraphs:
                    for run in p.runs: run.bold = True
            
            for inst in inst_data:
                row = table.add_row()
                row.cells[0].text = inst.get("REF. NO") or inst.get("ref_no") or ""
                row.cells[1].text = inst.get("instruction_issued", "")
                row.cells[2].text = inst.get("date", "")
                row.cells[3].text = inst.get("INSTRUCTIONS GIVEN BY") or inst.get("issued_by") or ""
            
            # Place after header
            inst_header_para._p.addnext(table._element)

        doc.save(output_path)
        return output_path

    def _set_table_borders(self, table):
        """Manually sets borders for a table using OXML (for templates missing styles)."""
        tbl = table._tbl
        tblPr = tbl.xpath('w:tblPr')[0]
        
        tblBorders = OxmlElement('w:tblBorders')
        for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'single')
            border.set(qn('w:sz'), '4') # 1/8 pt
            border.set(qn('w:space'), '0')
            border.set(qn('w:color'), '000000')
            tblBorders.append(border)
        
        tblPr.append(tblBorders)

    def _set_table_title(self, doc, table, title):
        """Finds the paragraph immediately before the table and sets its text."""
        # Find the table index in the document
        tbl_idx = -1
        for i, element in enumerate(doc.element.body):
            if element == table._element:
                tbl_idx = i
                break
        
        if tbl_idx > 0:
            # Look at previous element
            prev_element = doc.element.body[tbl_idx - 1]
            if prev_element.tag.endswith('p'):
                # It's a paragraph, update its text
                for para in doc.paragraphs:
                    if para._p == prev_element:
                        para.text = title
                        # Optional: Make it bold
                        if para.runs:
                            para.runs[0].bold = True
                        break

    def _set_cell_text(self, cell, text):
        """Helper to set text in a cell properly."""
        cell.text = ""
        p = cell.paragraphs[0]
        run = p.add_run(text)
        run.bold = True
