from docx import Document
import os

class ReportGenerator:
    """
    Main class for injecting AI-extracted data and manual user inputs into 
    Microsoft Word (.docx) templates. Designed for high-fidelity preservation 
     of logos, static text, and specifically requested static photo sections.
    """
    
    def __init__(self, template_path):
        self.template_path = template_path

    def _find_all_tables_by_header(self, doc, header_text):
        """
        Helper to locate Word tables by scanning the text of the first cell.
        Used to find slots for Labour, Weather, and Contract Details.
        """
        tables = []
        for table in doc.tables:
            if len(table.rows) > 0:
                # Normalize text to handle spacing/case differences
                first_cell_text = table.rows[0].cells[0].text.upper().strip()
                if header_text.upper() in first_cell_text:
                    tables.append(table)
        return tables

    def _update_cover_and_details(self, doc, data):
        """Replaces DATE: markers and fills Section A contract metrics."""
        report_period = data.get("report_date", "6th – 12th April 2026")
        
        # 1. Global Paragraph Replacement (Cover & Section E)
        for para in doc.paragraphs:
            if "DATE:" in para.text.upper():
                para.text = para.text.replace("DATE:", f"DATE: {report_period}")

        # 2. Section A (Table 0) Metrics
        tables = doc.tables
        if len(tables) > 0:
            t0 = tables[0]
            mapping = {
                "Time Lapsed in Weeks": data.get("time_elapsed", ""),
                "% contract period elapsed": data.get("pct_period", "") or data.get("pct_elapsed", ""),
                "% work done": data.get("pct_work", ""),
                "Date of this Report": report_period
            }
            for row in t0.rows:
                label = row.cells[0].text.strip()
                for key, val in mapping.items():
                    if key.lower() in label.lower():
                        row.cells[-1].text = str(val)

        # 3. Section E Marker (T3 Row 1)
        if len(tables) > 3:
            t3 = tables[3]
            if len(t3.rows) > 1:
                for cell in t3.rows[1].cells:
                    if "DATE:" in cell.text.upper():
                        cell.text = f"DATE: {report_period}"

    def generate_report(self, output_path, data, report_type="WEEKLY"):
        """High-fidelity generation mapping AI data to specific project tables."""
        doc = Document(self.template_path)
        
        # 0. Prepare Dates for the week
        report_period = data.get("report_date", "6th – 12th April 2026")
        week_dates = self._calculate_week_dates(report_period)

        # 1. Cover & Markers
        self._update_cover_and_details(doc, data)

        # 2. Section F: WORKS CARRIED OUT (Table 4)
        if len(doc.tables) > 4:
            self._fill_work_progress_table(doc.tables[4], data.get("works_by_day", []), week_dates)

        # 3. Section G: MATERIALS DELIVERED (Table 5)
        mat_tables = self._find_all_tables_by_header(doc, "Description")
        if mat_tables:
            self._fill_materials_table(mat_tables[0], data.get("materials_sum", {}))

        # 4. Section H: MACHINES (Table 6)
        plant_tables = self._find_all_tables_by_header(doc, "QTY")
        if plant_tables:
            self._fill_machinery_table(plant_tables[0], data.get("machinery", {}))

        # 5. LABOUR TURNOVER (Table 7)
        lab_tables = self._find_all_tables_by_header(doc, "CATEGORY")
        if lab_tables:
            self._fill_labour_table(lab_tables[0], data.get("labour", {}))

        # 6. SITE INSTRUCTIONS (Table 8)
        inst_tables = self._find_all_tables_by_header(doc, "REF. NO")
        if inst_tables:
            self._fill_instructions_table(inst_tables[0], data.get("instructions", []))

        # 7. INTERNS (Table 9)
        intern_tables = self._find_all_tables_by_header(doc, "Mon")
        if intern_tables:
            self._fill_interns_table(intern_tables[0], data.get("interns", []))

        # 8. WEATHER (Table 10)
        weather_tables = self._find_all_tables_by_header(doc, "CONDITION")
        if weather_tables:
            self._fill_weather_table(weather_tables[0], data.get("weather", []))

        # 9. TEXT SECTIONS (N, O, P, Security)
        self._fill_text_sections(doc, data)

        # 10. SUMMARY OF WORK DONE (Table 11)
        summary_tables = self._find_all_tables_by_header(doc, "SUMMARY TO DATE")
        if summary_tables:
            self._fill_summary_works_table(summary_tables[0], data.get("summary_to_date", {}))

        doc.save(output_path)
        return output_path

    def _calculate_week_dates(self, period_str):
        """Parses '6th – 12th April 2026' into individual dates."""
        import re
        try:
            match = re.search(r"(\d+).*?(\d+).*?(\w+)\s+(\d+)", period_str)
            if match:
                start_day = int(match.group(1))
                month = match.group(3)
                year = match.group(4)
                # This is a simplification. In production, use dateutil
                return [f"{start_day+i}/04/2026" for i in range(7)]
        except: pass
        return ["DATE:"] * 7

    def _fill_labour_table(self, table, labour_data):
        """Fills the matrix. Clears all cells first to remove template junk."""
        for row in table.rows[1:]:
            # Clear all Mon-Sun columns (1 to 7)
            for col_idx in range(1, 8):
                if col_idx < len(row.cells): row.cells[col_idx].text = "0"
            
            cat = row.cells[0].text.strip().upper().replace(" ", "")
            for ai_cat, values in labour_data.items():
                if ai_cat.strip().upper().replace(" ", "") in cat:
                    for i, val in enumerate(values):
                        if i + 1 < len(row.cells):
                            if isinstance(val, dict):
                                row.cells[i+1].text = f"D:{val.get('Day','0')} N:{val.get('Night','0')}"
                            else:
                                row.cells[i+1].text = str(val)

    def _fill_weather_table(self, table, weather_data):
        """Populates the morning/afternoon/evening conditions."""
        if not table: return
        for i, row in enumerate(table.rows[1:]):
            if i < len(weather_data):
                w = weather_data[i]
                if len(row.cells) >= 5:
                    row.cells[1].text = w.get("morning", "-")
                    row.cells[2].text = w.get("afternoon", "-")
                    row.cells[3].text = w.get("evening", "-")
                    row.cells[4].text = w.get("condition", "-")

    def _fill_work_progress_table(self, table, works, dates):
        """Maps daily works into the Mon-Sun rows with calculated dates."""
        days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
        for i in range(7):
            if i + 1 < len(table.rows):
                row = table.rows[i+1]
                row.cells[0].text = f"{days[i]} ({dates[i]})"
                row.cells[1].text = works[i] if i < len(works) else ""

    def _fill_interns_table(self, table, intern_data):
        """Fills Table 9 (Mon-Sun) for Interns. Clears junk first."""
        # Clear existing rows (except labels)
        for row in table.rows[1:]:
            for j in range(len(row.cells)): row.cells[j].text = "0"
        
        # Impute data by mapping categories
        for day_idx, daily_interns in enumerate(intern_data):
            for cat, qty in daily_interns.items():
                found = False
                for row in table.rows[1:]:
                    if cat.upper() in row.cells[0].text.upper():
                        row.cells[day_idx].text = str(qty)
                        found = True
                        break
                if not found:
                    new_row = table.add_row()
                    for j in range(len(new_row.cells)): new_row.cells[j].text = "0"
                    new_row.cells[0].text = cat
                    if day_idx < len(new_row.cells): new_row.cells[day_idx].text = str(qty)

    def _fill_instructions_table(self, table, instructions):
        """REF. NO | INSTRUCTION ISSUED | DATE | INSTRUCTIONS GIVEN BY:"""
        for i, inst in enumerate(instructions):
            row = table.rows[i+1] if i + 1 < len(table.rows) else table.add_row()
            row.cells[0].text = getattr(inst, 'ref_no', '-')
            row.cells[1].text = getattr(inst, 'instruction_issued', '-')
            row.cells[2].text = getattr(inst, 'date', '-')
            row.cells[3].text = getattr(inst, 'issued_by', '-')

    def _fill_text_sections(self, doc, data):
        """Appends daily logs for Security, H&S, Visitors, Challenges."""
        sections = {
            "N.\tHEALTH AND SAFETY": data.get("health_safety", []),
            "O.\tVISITORS": [f"{v.get('name')} - {v.get('purpose')}" for v in data.get("visitors", [])],
            "P.\tCHALLENGES": data.get("challenges", []),
            "M.\tSECURITY": data.get("security", [])
        }
        for header, lines in sections.items():
            for i, para in enumerate(doc.paragraphs):
                if header in para.text.upper():
                    for line in lines:
                        if line:
                            doc.paragraphs[i].insert_paragraph_after(f"• {line}")
                    break

    def _fill_materials_table(self, table, materials):
        """Populates the summed materials in Table 5."""
        for i, (name, m_data) in enumerate(materials.items()):
            qty_text = f"{m_data['qty']} {m_data['unit']}".strip()
            if i + 1 < len(table.rows):
                row = table.rows[i+1]
                row.cells[1].text = name
                row.cells[2].text = qty_text
            else:
                row = table.add_row()
                row.cells[1].text = name
                row.cells[2].text = qty_text

    def _fill_machinery_table(self, table, machinery):
        """Updates machinery status in Table 6."""
        for row in table.rows[1:]:
            name = row.cells[1].text.strip().upper()
            if name in machinery:
                row.cells[2].text = str(machinery[name]["qty"])
                row.cells[3].text = machinery[name]["status"]

    def _fill_summary_works_table(self, table, summary_data):
        """Dynamic expansion of the 'Summary of Work Done to Date' section."""
        for i, (component, description) in enumerate(summary_data.items()):
            row = table.rows[i+1] if i + 1 < len(table.rows) else table.add_row()
            row.cells[1].text = component
            row.cells[3].text = description
