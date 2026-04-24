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
        """
        1. Searches for specific labels in the document text (Cover Page).
        2. Updates the 'Contract Details' table (Table 1) using manual inputs.
        """
        # --- PHASE A: COVER PAGE REPLACEMENT ---
        # We look for common patterns like 'WEEK 20 PROGRESS REPORT' or dates
        for para in doc.paragraphs:
            # Update the main Report Title
            if "PROGRESS REPORT" in para.text.upper() and data.get("title"):
                para.text = data["title"]
            
            # Update the Reporting Period/Date on the cover
            # We look for paragraphs that look like 'APRIL 2026' or 'MARCH 2026'
            if "2026" in para.text and data.get("report_date"):
                # We limit the length to avoid replacing large body text blocks
                if len(para.text) < 50: 
                    para.text = data["report_date"]

        # --- PHASE B: CONTRACT DETAILS TABLE ---
        # This matches items 14, 15, 16, and 17 as per your requirement
        tables = self._find_all_tables_by_header(doc, "PROJECT TITLE")
        if not tables: return
        table = tables[0]

        mapping = {
            "14. Time Lapsed in Weeks": data.get("time_elapsed"),
            "15. % Contract Period Elapsed": data.get("pct_period"),
            "16. % Work Done": data.get("pct_work"),
            "17. Date of this Report": data.get("report_date"),
            "17. Reporting Period": data.get("report_date") # Handles monthly variations
        }

        for row in table.rows:
            label_cell = row.cells[0].text.strip()
            for label, value in mapping.items():
                if label.upper() in label_cell.upper() and value:
                    # Update the value cell (assumes it is the last cell in the row)
                    row.cells[-1].text = str(value)

    def generate_report(self, output_path, data, report_type="WEEKLY"):
        """
        End-to-end report generation.
        Fills dynamic tables while PROTECTING static sections (Materials on Site/Photos).
        """
        doc = Document(self.template_path)

        # 1. Update Title and Contract Table (The manual project metrics)
        self._update_cover_and_details(doc, data)

        # 2. Update Labour Turnover Tables (Data extracted from 7 Dailies or 4 Weeklies)
        lab_tables = self._find_all_tables_by_header(doc, "CATEGORY")
        for i, table in enumerate(lab_tables):
            # If Monthly, we fill the 4 slots sequentially. If Weekly, just the first.
            week_data = data["weeks"][i] if report_type == "MONTHLY" and "weeks" in data else data
            self._fill_labour_table(table, week_data.get("labour", {}))

        # 3. Update Weather Summary Tables
        weather_tables = self._find_all_tables_by_header(doc, "DAY")
        for i, table in enumerate(weather_tables):
            week_data = data["weeks"][i] if report_type == "MONTHLY" and "weeks" in data else data
            self._fill_weather_table(table, week_data.get("weather", []))

        # --- CRITICAL SAFEGUARD ---
        # Note: 'MATERIALS ON SITE' and 'PROGRESS PHOTOS' are left entirely untouched.
        # This preserves the existing photos and static layout in your template.
        # You will manually add the new photos after downloading.

        doc.save(output_path)
        return output_path

    def _fill_labour_table(self, table, labour_data):
        """Standardizes and fills the workforce turnover matrix."""
        for row in table.rows[1:]: # Skip the header row
            doc_cat = row.cells[0].text.strip().upper().replace(" ", "")
            for ai_cat, counts in labour_data.items():
                # Fuzzy match category names (e.g. 'Steel Fixer' vs 'STEEL FIXERS')
                if ai_cat.strip().upper().replace(" ", "") in doc_cat:
                    for i, count in enumerate(counts):
                        if i + 1 < len(row.cells):
                            row.cells[i+1].text = str(count)

    def _fill_weather_table(self, table, weather_data):
        """Populates the morning/afternoon weather conditions."""
        for i, row in enumerate(table.rows[1:]):
            if i < len(weather_data):
                w = weather_data[i]
                if len(row.cells) >= 3:
                    row.cells[1].text = w.get("morning", "-")
                    row.cells[2].text = w.get("afternoon", "-")
