from docx import Document
import os
import re
from datetime import datetime, timedelta


class ReportGenerator:
    """
    Injects AI-extracted weekly JSON data into a Microsoft Word (.docx) template.
    Finds sections by scanning table headers — robust to template reordering.
    """

    def __init__(self, template_path):
        self.template_path = template_path

    # ─────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────

    def _find_table_by_header(self, doc, header_text):
        """Find the first table whose first cell contains header_text."""
        for table in doc.tables:
            if table.rows:
                first = table.rows[0].cells[0].text.upper().strip()
                if header_text.upper() in first:
                    return table
        return None

    def _calculate_week_dates(self, period_str):
        """
        Parse '13th – 19th April 2026' → list of 7 date strings like '13/04/2026'.
        Also returns week number string if present (e.g. 'WEEK 21').
        """
        try:
            # Remove ordinal suffixes: 13th → 13
            cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", period_str, flags=re.IGNORECASE)
            # Match: start_day – end_day Month Year
            m = re.search(r"(\d+)\s*[–\-]\s*(\d+)\s+(\w+)\s+(\d{4})", cleaned)
            if m:
                start_day = int(m.group(1))
                month_str = m.group(3)
                year = int(m.group(4))
                month_num = datetime.strptime(month_str, "%B").month
                base = datetime(year, month_num, start_day)
                return [( base + timedelta(days=i)).strftime("%d/%m/%Y") for i in range(7)]
        except Exception:
            pass
        return ["-"] * 7

    def _extract_week_number(self, period_str):
        """Try to extract week number from the JSON or fall back to a placeholder."""
        # e.g. "6th – 12th April 2026" — week number is not in the JSON directly.
        # Return empty so user can fill it, or derive from date vs commencement.
        return ""

    # ─────────────────────────────────────────────────────────────
    # MAIN ENTRY POINT
    # ─────────────────────────────────────────────────────────────

    def generate_report(self, output_path, data, report_type="WEEKLY"):
        """High-fidelity generation mapping AI JSON data to Word template sections."""
        doc = Document(self.template_path)

        report_period = data.get("report_date", "")
        week_dates = self._calculate_week_dates(report_period)

        # 1. Cover page — WEEK _ / DATE: paragraphs
        self._fill_cover_dates(doc, report_period)

        # 2. Table 3 — Section E header row (DATE: across 3 cols)
        self._fill_section_e_date(doc, report_period)

        # 3. Table 4 — Section F: Works Carried Out (DAY | WORK DONE)
        works_table = self._find_table_by_header(doc, "DAY")
        if works_table:
            self._fill_work_progress_table(works_table, data.get("works_by_day", {}), week_dates)

        # 4. Table 5 — Section G: Materials Delivered
        mat_table = self._find_table_by_header(doc, "Description")
        if mat_table:
            self._fill_materials_table(mat_table, data.get("materials_sum", {}))

        # 5. Table 6 — Section H: Plant & Machinery
        plant_table = self._find_table_by_header(doc, "QTY")
        if plant_table:
            self._fill_machinery_table(plant_table, data.get("machinery", {}))

        # 6. Table 7 — Labour Turnover (CATEGORY | Mon | Tue | ... | Sun)
        lab_table = self._find_table_by_header(doc, "CATEGORY")
        if lab_table:
            self._fill_labour_table(lab_table, data.get("labour", {}))

        # 7. Table 8 — Site Instructions (REF. NO | INSTRUCTION | DATE | BY)
        inst_table = self._find_table_by_header(doc, "REF. NO")
        if inst_table:
            self._fill_instructions_table(inst_table, data.get("instructions", []))

        # 8. Table 9 — Interns (Mon | Tue | Wed | Thur | Fri | Sat | Sun)
        intern_table = self._find_table_by_header(doc, "Mon")
        if intern_table:
            self._fill_interns_table(intern_table, data.get("interns", []))

        # 9. Table 10 — Weather (DAY | MORNING | AFTERNOON | EVENING | CONDITION)
        weather_table = self._find_table_by_header(doc, "CONDITION")
        if weather_table:
            self._fill_weather_table(weather_table, data.get("weather", []))

        # 10. Paragraph text sections: N(Health&Safety), M(Security), P(Challenges)
        self._fill_text_sections(doc, data)

        # 11. Table 11 — Summary of Works Done to Date
        summary_table = self._find_table_by_header(doc, "SUMMARY OF WORK")
        if summary_table:
            self._fill_summary_works_table(summary_table, data.get("summary_to_date", {}))

        doc.save(output_path)
        print(f"[OK] Report saved to: {output_path}")
        return output_path

    # ─────────────────────────────────────────────────────────────
    # SECTION FILLERS
    # ─────────────────────────────────────────────────────────────

    def _fill_cover_dates(self, doc, report_period):
        """Fill 'WEEK _ PROGRESS REPORT' and 'DATE:' paragraphs on the cover page."""
        for para in doc.paragraphs:
            text_upper = para.text.upper().strip()
            # Cover title — "WEEK _ PROGRESS REPORT"
            if "WEEK" in text_upper and "PROGRESS REPORT" in text_upper:
                # Preserve formatting by replacing run text
                for run in para.runs:
                    if "_" in run.text:
                        run.text = run.text.replace("_", "")  # blank for user to fill week no.
            # Cover date line — "DATE:"
            elif text_upper == "DATE:":
                for run in para.runs:
                    if "DATE:" in run.text.upper():
                        run.text = f"DATE: {report_period}"
                        break

    def _fill_section_e_date(self, doc, report_period):
        """Fill Table 3 Row 1: DATE: cells (appears before the works table)."""
        for table in doc.tables:
            if table.rows and "DATE:" in table.rows[0].cells[0].text.upper():
                for cell in table.rows[0].cells:
                    if "DATE:" in cell.text.upper():
                        cell.text = f"DATE: {report_period}"
                break
            # Also check row 1 in Table 3 (header has PROJECT:)
            if table.rows and "PROJECT:" in table.rows[0].cells[0].text.upper():
                for row in table.rows:
                    if "DATE:" in row.cells[0].text.upper():
                        for cell in row.cells:
                            cell.text = f"DATE: {report_period}"
                        break

    def _fill_work_progress_table(self, table, works_by_day, week_dates):
        """
        Table 4: DAY | WORK DONE
        works_by_day is a dict: {"Block Type B": "• ...", "Kindergarten": "• ..."}
        The template has one row per day (Mon–Sun). We concatenate all blocks per row.
        """
        day_labels = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

        # Merge all block summaries into one text block (each block on a new line)
        all_works_text = "\n".join(
            f"{block}:\n{summary}" for block, summary in works_by_day.items()
        ) if works_by_day else ""

        for i, row in enumerate(table.rows[1:8]):  # rows 1–7 = Mon–Sun
            day_label = day_labels[i] if i < len(day_labels) else f"DAY {i+1}"
            date_str = week_dates[i] if i < len(week_dates) else "-"
            # Fill day cell
            row.cells[0].text = f"{day_label}\n({date_str})"
            # Fill works cell — same aggregated text for all days
            # (works_by_day is a weekly summary, not per-day; put full summary in each row)
            row.cells[1].text = all_works_text

    def _fill_labour_table(self, table, labour_data):
        """
        Table 7: CATEGORY | Mon | Tue | Wed | Thur | Fri | Sat | Sun
        labour_data: {"Site Agent/PM": ["1(m)","1(m)",...], ...}
        Matches by comparing template row label to canonical key (case-insensitive).
        """
        DAY_COLS = {"mon": 1, "tue": 2, "wed": 3, "thur": 4, "fri": 5, "sat": 6, "sun": 7}

        # Clear all data cells first
        for row in table.rows[1:]:
            for col_idx in range(1, 8):
                if col_idx < len(row.cells):
                    row.cells[col_idx].text = "0"

        for row in table.rows[1:]:
            cat_label = row.cells[0].text.strip().upper().replace(" ", "").replace("&", "AND")
            for ai_cat, values in labour_data.items():
                ai_norm = ai_cat.strip().upper().replace(" ", "").replace("&", "AND")
                if cat_label == ai_norm or cat_label in ai_norm or ai_norm in cat_label:
                    for i, val in enumerate(values):
                        col_idx = i + 1  # Mon=1, Tue=2 ... Sun=7
                        if col_idx < len(row.cells):
                            row.cells[col_idx].text = str(val)
                    break

        # Append any extra categories (dynamic) not in the template
        canonical_in_template = {
            row.cells[0].text.strip().upper().replace(" ", "")
            for row in table.rows[1:]
        }
        for ai_cat, values in labour_data.items():
            ai_norm = ai_cat.strip().upper().replace(" ", "").replace("&", "AND")
            if not any(ai_norm in t or t in ai_norm for t in canonical_in_template):
                new_row = table.add_row()
                new_row.cells[0].text = ai_cat
                for i, val in enumerate(values):
                    col_idx = i + 1
                    if col_idx < len(new_row.cells):
                        new_row.cells[col_idx].text = str(val)

    def _fill_weather_table(self, table, weather_data):
        """Table 10: DAY | MORNING | AFTERNOON | EVENING | CONDITION"""
        for i, row in enumerate(table.rows[1:]):
            if i < len(weather_data):
                w = weather_data[i]
                if len(row.cells) >= 5:
                    row.cells[1].text = w.get("morning", "-")
                    row.cells[2].text = w.get("afternoon", "-")
                    row.cells[3].text = w.get("evening", "-")
                    row.cells[4].text = w.get("condition", "-")

    def _fill_materials_table(self, table, materials):
        """Table 5: S/NO | Description | Quantity"""
        for i, (name, m_data) in enumerate(materials.items()):
            qty_text = f"{m_data['qty']} {m_data.get('unit', '')}".strip()
            if i + 1 < len(table.rows):
                row = table.rows[i + 1]
            else:
                row = table.add_row()
            row.cells[0].text = str(i + 1)
            row.cells[1].text = name.title()
            row.cells[2].text = qty_text

    def _fill_machinery_table(self, table, machinery):
        """Table 6: S/N | Description | QTY | Status — match by description."""
        for row in table.rows[1:]:
            name = row.cells[1].text.strip().upper()
            for m_name, m_data in machinery.items():
                if m_name.upper() in name or name in m_name.upper():
                    row.cells[2].text = str(m_data.get("qty", ""))
                    row.cells[3].text = m_data.get("status", "Idle")
                    break

    def _fill_instructions_table(self, table, instructions):
        """Table 8: REF. NO | INSTRUCTION ISSUED | DATE | INSTRUCTIONS GIVEN BY"""
        valid = [inst for inst in instructions if isinstance(inst, dict) and inst.get("instruction_issued", "").strip() not in ("", "None")]
        for i, inst in enumerate(valid):
            if i + 1 < len(table.rows):
                row = table.rows[i + 1]
            else:
                row = table.add_row()
            row.cells[0].text = str(inst.get("REF. NO", ""))
            row.cells[1].text = str(inst.get("instruction_issued", ""))
            row.cells[2].text = str(inst.get("date", ""))
            row.cells[3].text = str(inst.get("INSTRUCTIONS GIVEN BY", ""))

    def _fill_interns_table(self, table, intern_data):
        """Table 9: Mon | Tue | Wed | Thur | Fri | Sat | Sun — one data row."""
        if not table.rows or len(table.rows) < 2:
            return
        data_row = table.rows[1]
        for col_idx in range(len(data_row.cells)):
            data_row.cells[col_idx].text = "0"

        for day_idx, daily in enumerate(intern_data[:7]):
            if not isinstance(daily, dict):
                continue
            # Try every key to find a count value
            for key, val in daily.items():
                num_match = re.search(r"\d+", str(val))
                if num_match and day_idx < len(data_row.cells):
                    data_row.cells[day_idx].text = num_match.group()
                    break

    def _fill_text_sections(self, doc, data):
        """
        Fill free-text paragraph sections: M(Security), N(H&S), P(Challenges).
        Values are now plain strings (not lists), so insert them directly after the header.
        """
        sections = {
            "M.\tSECURITY":          data.get("security", ""),
            "N.\tHEALTH AND SAFETY": data.get("health_safety", ""),
            "P.\tCHALLENGES":        data.get("challenges", ""),
            "O.\tVISITORS":          f"Total visitors this week: {data.get('total_visitors_count', 0)}",
        }
        for header, content in sections.items():
            if not content:
                continue
            for i, para in enumerate(doc.paragraphs):
                if header.upper().replace("\t", " ") in para.text.upper().replace("\t", " "):
                    # Insert text after this paragraph
                    new_para = para.insert_paragraph_after(str(content))
                    break

    def _fill_summary_works_table(self, table, summary_data):
        """
        Table 11: SUMMARY OF WORK DONE TO DATE (2 cols: Block | Description)
        Matches existing rows by block name, appends new rows for new blocks.
        """
        # Build lookup of existing template rows
        existing = {}
        for row in table.rows[1:]:
            key = row.cells[0].text.strip().upper()
            if key:
                existing[key] = row

        for component, description in summary_data.items():
            key = component.strip().upper()
            if key in existing:
                existing[key].cells[1].text = str(description)
            else:
                new_row = table.add_row()
                new_row.cells[0].text = component
                new_row.cells[1].text = str(description)
