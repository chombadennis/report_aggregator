"""
generator.py
------------
Injects AI-extracted weekly JSON data into the Word (.docx) template.
No AI calls — pure JSON → Word mapping.
"""

from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os
import re
from datetime import datetime, timedelta
import copy


class ReportGenerator:

    def __init__(self, template_path):
        self.template_path = template_path

    # ─── HELPERS ──────────────────────────────────────────────────────────────

    def _find_table_by_any_header_cell(self, doc, header_text):
        """Find the first table where ANY cell in the first row contains header_text."""
        for table in doc.tables:
            if table.rows:
                for cell in table.rows[0].cells:
                    if header_text.upper() in cell.text.upper():
                        return table
        return None

    def _find_interns_table(self, doc):
        """
        Find the Interns table specifically: a 7-column table whose header row
        contains Mon/Tue/Wed day names but does NOT have a 'CATEGORY' column.
        This distinguishes it from the Labour table which also has day headers.
        """
        for table in doc.tables:
            if not table.rows:
                continue
            header_texts = [c.text.strip().upper() for c in table.rows[0].cells]
            has_day_headers = any(d in header_texts for d in ["MON", "TUE", "WED"])
            has_category    = any("CATEGORY" in h for h in header_texts)
            # Interns table: 7 cols (Mon-Sun only), no CATEGORY column, exactly 2 rows
            if has_day_headers and not has_category and len(table.columns) == 7:
                return table
        return None

    def _find_para_by_text(self, doc, search_text):
        """Find the first paragraph containing search_text (case-insensitive)."""
        for i, para in enumerate(doc.paragraphs):
            if search_text.upper() in para.text.upper():
                return i, para
        return None, None

    def _calculate_week_dates(self, period_str):
        """'13th – 19th April 2026' → ['13/04/2026', '14/04/2026', ...]"""
        try:
            cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", period_str, flags=re.IGNORECASE)
            m = re.search(r"(\d+)\s*[–\-]\s*(\d+)\s+(\w+)\s+(\d{4})", cleaned)
            if m:
                start_day = int(m.group(1))
                month_str = m.group(3)
                year = int(m.group(4))
                month_num = datetime.strptime(month_str, "%B").month
                base = datetime(year, month_num, start_day)
                return [(base + timedelta(days=i)).strftime("%d/%m/%Y") for i in range(7)]
        except Exception:
            pass
        return ["-"] * 7

    def _insert_row_before_last(self, table):
        """Insert a new empty row before the last row (TOTAL) using lxml."""
        last_tr = table.rows[-1]._tr
        new_tr = copy.deepcopy(table.rows[-2]._tr)
        # Clear all cell text in the new row
        for tc in new_tr.findall(qn('w:tc')):
            for t_elem in tc.findall('.//' + qn('w:t')):
                t_elem.text = ''
        # Insert immediately before the TOTAL row using lxml's addprevious
        last_tr.addprevious(new_tr)
        return table.rows[-2]  # The newly inserted row

    def _normalize_document_formatting(self, doc):
        """
        Clears manual indentation overrides from Section E onwards and left-aligns
        tables 3 to 10 to ensure a beautiful and consistent layout.
        """
        from docx.enum.table import WD_TABLE_ALIGNMENT
        
        # 1. Normalize tables 3 to 10 only (these are the ones from Section E to Weather)
        for idx, table in enumerate(doc.tables):
            if 3 <= idx <= 10:
                table.alignment = WD_TABLE_ALIGNMENT.LEFT
                
                tblPr = table._tbl.tblPr
                tblInds = tblPr.xpath('w:tblInd')
                if tblInds:
                    for tblInd in tblInds:
                        tblPr.remove(tblInd)
                
                new_tblInd = OxmlElement('w:tblInd')
                new_tblInd.set(qn('w:w'), '0')
                new_tblInd.set(qn('w:type'), 'dxa')
                tblPr.append(new_tblInd)
                
        # 2. Normalize paragraphs starting from Section E onwards
        # Find the start paragraph of Section E dynamically
        start_normalize_idx = 33 # default fallback
        for idx, para in enumerate(doc.paragraphs):
            text = para.text.upper().strip()
            if "E." in text and "PROGRESS" in text:
                start_normalize_idx = idx
                break
                
        for idx, para in enumerate(doc.paragraphs):
            if idx >= start_normalize_idx:
                pPr = para._p.get_or_add_pPr()
                ind_elems = pPr.xpath('w:ind')
                if ind_elems:
                    for ind in ind_elems:
                        pPr.remove(ind)
                        
                para.paragraph_format.left_indent = None
                para.paragraph_format.first_line_indent = None
                para.paragraph_format.right_indent = None

    # ─── MAIN ENTRY ───────────────────────────────────────────────────────────

    def generate_report(self, output_path, data, report_type="WEEKLY"):
        doc = Document(self.template_path)

        report_period = data.get("report_date", "")
        week_dates = self._calculate_week_dates(report_period)

        # 1. Cover date paragraphs
        self._fill_cover_dates(doc, report_period, data.get("title", ""))

        # 2. Section A — Contract Details (Table 0)
        self._fill_contract_details(doc, data)

        # 3. Section E date row in Table 3
        self._fill_section_e_date(doc, report_period)

        # 3. Section F — Works Carried Out (Table 4: DAY | WORK DONE)
        works_table = self._find_table_by_any_header_cell(doc, "WORK DONE")
        if works_table:
            self._fill_work_progress_table(works_table, data.get("works_by_day", {}), week_dates)

        # 4. Section G — Materials Delivered (Table 5: S/NO | Description | Quantity)
        mat_table = self._find_table_by_any_header_cell(doc, "Description")
        if mat_table:
            self._fill_materials_table(mat_table, data.get("materials_sum", {}))

        # 5. Section H — Machinery (Table 6: S/N | Description | QTY | Status)
        plant_table = self._find_table_by_any_header_cell(doc, "Status")
        if plant_table:
            self._fill_machinery_table(plant_table, data.get("machinery", {}))

        # 6. Labour Turnover (Table 7: CATEGORY | Mon..Sun)
        lab_table = self._find_table_by_any_header_cell(doc, "CATEGORY")
        if lab_table:
            self._fill_labour_table(lab_table, data.get("labour", {}))

        # 7. Site Instructions (Table 8: REF. NO | INSTRUCTION | DATE | BY)
        inst_table = self._find_table_by_any_header_cell(doc, "REF. NO")
        if inst_table:
            self._fill_instructions_table(inst_table, data.get("instructions", []))

        # 8. Interns (Table 9: Mon | Tue | Wed | Thur | Fri | Sat | Sun)
        intern_table = self._find_interns_table(doc)
        if intern_table:
            self._fill_interns_table(intern_table, data.get("interns", []))

        # 9. Weather (Table 10: DAY | MORNING | AFTERNOON | EVENING | CONDITION)
        weather_table = self._find_table_by_any_header_cell(doc, "CONDITION")
        if weather_table:
            self._fill_weather_table(weather_table, data.get("weather", []))

        # 10. Text sections: Security, H&S, Visitors, Challenges
        self._fill_text_sections(doc, data)

        # 11. Summary of Works Done to Date (Table 11)
        summary_table = self._find_table_by_any_header_cell(doc, "SUMMARY OF WORK")
        if summary_table:
            self._fill_summary_works_table(summary_table, data.get("summary_to_date", {}))

        # 12. Normalize document layout formatting (indentation and alignment)
        self._normalize_document_formatting(doc)

        # Delete old output and save fresh
        if os.path.exists(output_path):
            os.remove(output_path)
        doc.save(output_path)
        print(f"[OK] Report saved to: {output_path}")
        return output_path

    # ─── SECTION FILLERS ──────────────────────────────────────────────────────

    def _fill_contract_details(self, doc, data):
        """
        Fill Table 0 (A. CONTRACT DETAILS) based on user input.
        Row 0: Project Title
        Row 13: 14. Time Lapsed in Weeks
        Row 14: 15. % contract period elapsed
        Row 15: 16. % work done
        Row 16: 17. Date of this Report
        """
        if not doc.tables:
            return
            
        table = doc.tables[0] # Table 0 is Contract Details
        
        # Mapping frontend keys to row indices in Table 0
        mapping = {
            "time_elapsed": 13,
            "pct_period": 14,
            "pct_work": 15,
            "report_date": 16
        }
        
        for key, row_idx in mapping.items():
            val = data.get(key, "").strip()
            if val and row_idx < len(table.rows):
                row = table.rows[row_idx]
                if len(row.cells) >= 3:
                    # Cell index 2 is where the values go
                    row.cells[2].text = val
                elif len(row.cells) == 2:
                    # Fallback for tables with 2 columns
                    row.cells[1].text = val

    def _fill_cover_dates(self, doc, report_period, report_title):
        """Fill WEEK _ PROGRESS REPORT / DATE: on cover page."""
        for para in doc.paragraphs:
            # 1. Update the Main Title (Para 15 in template)
            if "WEEK _ PROGRESS REPORT" in para.text.upper() or "PROGRESS REPORT" in para.text.upper():
                # If we have a custom title from frontend, use it.
                if report_title:
                    # Clear and set new text
                    para.text = report_title
            
            # 2. Update the DATE: field
            if para.text.strip().upper() == "DATE:":
                for run in para.runs:
                    if "DATE:" in run.text.upper():
                        run.text = f"DATE: {report_period}"
                        break

    def _fill_section_e_date(self, doc, report_period):
        """Fill Table 3 DATE: row (3 cells)."""
        for table in doc.tables:
            if not table.rows:
                continue
            for row in table.rows:
                if row.cells and "DATE:" in row.cells[0].text.upper():
                    for cell in row.cells:
                        if "DATE:" in cell.text.upper():
                            cell.text = f"DATE: {report_period}"

    def _fill_work_progress_table(self, table, works_by_day, week_dates):
        """
        Table 4 — DAY | WORK DONE.
        works_by_day is now keyed by day name: {"Monday": {"Component": "• task\n• task", ...}, ...}
        Each day row gets its own unique per-component content with bullet lines split per paragraph.
        """
        day_labels = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
        day_keys   = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for i, row in enumerate(table.rows[1:8]):
            day_label = day_labels[i] if i < len(day_labels) else f"DAY {i+1}"
            date_str  = week_dates[i] if i < len(week_dates) else "-"
            row.cells[0].text = f"{day_label}\n({date_str})"

            # Fetch this day's component dict from the new per-day structure
            day_key = day_keys[i] if i < len(day_keys) else ""
            day_components = works_by_day.get(day_key, {})

            # Build rich content in the WORK DONE cell
            cell = row.cells[1]
            for p in cell.paragraphs:
                p.clear()

            if not day_components:
                cell.paragraphs[0].add_run("No works recorded.")
                continue

            first_block = True
            for block_name, summary_text in day_components.items():
                # Clean the heading (remove any accidental bullets from the string)
                heading_text = block_name.replace("•", "").strip()
                
                # Add a new paragraph for the heading
                key_para = cell.paragraphs[0] if first_block else cell.add_paragraph()
                
                # Reduce space between categories: Pt(4) instead of Pt(6) or empty paragraphs
                key_para.paragraph_format.space_before = Pt(0) if first_block else Pt(4)
                key_para.paragraph_format.space_after = Pt(1)
                
                key_run = key_para.add_run(heading_text + ":")
                key_run.bold = True

                # Activities — each '\n'-separated line gets its own bullet paragraph
                bullet_lines = str(summary_text).split("\n")
                for line in bullet_lines:
                    line = line.strip()
                    if not line:
                        continue
                    # Ensure it has exactly one bullet
                    clean_line = line.lstrip("•").strip()
                    bullet_para = cell.add_paragraph(f"• {clean_line}")
                    bullet_para.paragraph_format.space_before = Pt(0)
                    bullet_para.paragraph_format.space_after = Pt(0)

                first_block = False

    def _fill_labour_table(self, table, labour_data):
        """
        Table 7 — CATEGORY | Mon | Tue | Wed | Thur | Fri | Sat | Sun.
        Matches by category name. Extra categories inserted BEFORE TOTAL row.
        TOTAL is always last.
        """
        # Clear all data cells first
        for row in table.rows[1:]:
            for col_idx in range(1, 8):
                if col_idx < len(row.cells):
                    row.cells[col_idx].text = "0"

        # Build set of category labels already in the template
        template_cats = {
            row.cells[0].text.strip().upper().replace(" ", "").replace("&", "AND"): row
            for row in table.rows[1:]
        }

        # Fill matching rows using a two-pass approach to prevent partial match hijacking
        # (e.g., preventing "Unskilled" from matching "Steel Unskilled" if an exact match exists)
        unmatched = {}
        used_rows = set()

        # Pass 1: Exact matches
        for ai_cat, values in labour_data.items():
            if ai_cat.strip().upper() == "TOTAL":
                continue
            ai_norm = ai_cat.strip().upper().replace(" ", "").replace("&", "AND")
            
            for tmpl_norm, row in template_cats.items():
                if ai_norm == tmpl_norm:
                    for i, val in enumerate(values):
                        col_idx = i + 1
                        if col_idx < len(row.cells):
                            row.cells[col_idx].text = str(val)
                    used_rows.add(tmpl_norm)
                    break

        # Pass 2: Fuzzy/Partial matches (only for rows not yet used)
        for ai_cat, values in labour_data.items():
            if ai_cat.strip().upper() == "TOTAL":
                continue
            ai_norm = ai_cat.strip().upper().replace(" ", "").replace("&", "AND")
            
            # Skip if we already matched this AI category in Pass 1
            already_matched = False
            for tmpl_norm in used_rows:
                if ai_norm == tmpl_norm:
                    already_matched = True
                    break
            if already_matched:
                continue

            matched = False
            for tmpl_norm, row in template_cats.items():
                if tmpl_norm in used_rows:
                    continue
                if ai_norm in tmpl_norm or tmpl_norm in ai_norm:
                    for i, val in enumerate(values):
                        col_idx = i + 1
                        if col_idx < len(row.cells):
                            row.cells[col_idx].text = str(val)
                    used_rows.add(tmpl_norm)
                    matched = True
                    break
            if not matched:
                unmatched[ai_cat] = values

        # Insert unmatched (extra) categories BEFORE the TOTAL row
        for ai_cat, values in unmatched.items():
            new_row = self._insert_row_before_last(table)
            new_row.cells[0].text = ai_cat
            for i, val in enumerate(values):
                col_idx = i + 1
                if col_idx < len(new_row.cells):
                    new_row.cells[col_idx].text = str(val)

        # Now fill the TOTAL row (always the last row)
        if "TOTAL" in labour_data:
            total_row = table.rows[-1]
            for i, val in enumerate(labour_data["TOTAL"]):
                col_idx = i + 1
                if col_idx < len(total_row.cells):
                    total_row.cells[col_idx].text = str(val)

    def _fill_weather_table(self, table, weather_data):
        """Table 10 — DAY | MORNING | AFTERNOON | EVENING | CONDITION"""
        for i, row in enumerate(table.rows[1:]):
            if i < len(weather_data):
                w = weather_data[i]
                if len(row.cells) >= 5:
                    row.cells[1].text = w.get("morning", "-")
                    row.cells[2].text = w.get("afternoon", "-")
                    row.cells[3].text = w.get("evening", "-")
                    row.cells[4].text = w.get("condition", "-")

    def _fill_materials_table(self, table, materials):
        """Table 5 — S/NO | Description | Quantity. Clears row 1 then fills/appends."""
        # Remove template placeholder rows (keep header only)
        while len(table.rows) > 1:
            tbl = table._tbl
            tbl.remove(table.rows[-1]._tr)

        for i, (name, m_data) in enumerate(materials.items()):
            qty_val = m_data.get("qty", 0)
            unit = m_data.get("unit", "")
            qty_text = f"{qty_val} {unit}".strip()
            row = table.add_row()
            row.cells[0].text = str(i + 1)
            row.cells[1].text = name.title()
            row.cells[2].text = qty_text

    def _fill_machinery_table(self, table, machinery):
        """Table 6 — S/N | Description | QTY | Status."""
        for row in table.rows[1:]:
            name = row.cells[1].text.strip().upper()
            for m_name, m_data in machinery.items():
                if m_name.upper() in name or name in m_name.upper():
                    row.cells[2].text = str(m_data.get("qty", ""))
                    row.cells[3].text = m_data.get("status", "Idle")
                    break

    def _fill_instructions_table(self, table, instructions):
        """Table 8 — REF. NO | INSTRUCTION ISSUED | DATE | INSTRUCTIONS GIVEN BY"""
        valid = [
            inst for inst in instructions
            if isinstance(inst, dict) and inst.get("instruction_issued", "").strip() not in ("", "None")
        ]
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
        """
        Table 9 — Mon | Tue | Wed | Thur | Fri | Sat | Sun.
        intern_data is a list of 7 dicts (one per day). Each dict may use any key
        (total, count, note, total_on_site, details, …). We scan every value for
        the first integer and write it into the corresponding day column.
        Empty dicts (no interns recorded that day) are written as '0'.
        """
        if len(table.rows) < 2:
            return
        data_row = table.rows[1]

        # Initialise all 7 day columns to '0'
        for col_idx in range(len(data_row.cells)):
            data_row.cells[col_idx].text = "0"

        for day_idx, daily in enumerate(intern_data[:7]):
            if day_idx >= len(data_row.cells):
                break
            if not isinstance(daily, dict) or not daily:
                # Empty dict means no interns recorded — leave as '0'
                continue
            # Scan every value in the dict for the first integer
            for val in daily.values():
                num_match = re.search(r"\d+", str(val))
                if num_match:
                    data_row.cells[day_idx].text = num_match.group()
                    break

    def _fill_text_sections(self, doc, data):
        """
        Fill paragraphs: SECURITY, HEALTH AND SAFETY, VISITORS, CHALLENGES.
        Inserts text immediately after the section header paragraph using lxml.
        Multi-line bullet content (\\n-separated) is written as separate paragraphs.
        """
        from docx.oxml import OxmlElement

        def _make_para_xml(text):
            """Create a bare w:p element containing a single w:r / w:t with the given text."""
            new_p = OxmlElement('w:p')
            new_r = OxmlElement('w:r')
            new_t = OxmlElement('w:t')
            new_t.text = text
            new_t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            new_r.append(new_t)
            new_p.append(new_r)
            return new_p

        def _insert_content_after(ref_para, content):
            """
            Insert one paragraph per line of content immediately after ref_para.
            Lines are inserted in reverse order so the first line ends up first.
            """
            lines = [l.strip() for l in str(content).split("\n") if l.strip()]
            if not lines:
                lines = [str(content)]
            # Insert in reverse so the reading order comes out correctly
            for line in reversed(lines):
                ref_para._p.addnext(_make_para_xml(line))

        # Section header → data key mapping.
        # IMPORTANT: Use 'HEALTH AND SAFETY.' (with the period) to distinguish the section
        # header at Para 66 from the phrase 'health and safety outcomes' in Para 32
        # (SOCIO-ECONOMIC IMPACT body text). Without the period the wrong paragraph is matched.
        section_map = [
            ("HEALTH AND SAFETY.",  data.get("health_safety", "")),
            ("SECURITY",            data.get("security", "")),
            ("VISITORS",            f"Total visitors this week: {data.get('total_visitors_count', 0)}"),
            ("CHALLENGES",          data.get("challenges", "")),
        ]

        for search_key, content in section_map:
            if not content:
                continue
            _, para = self._find_para_by_text(doc, search_key)
            if para:
                _insert_content_after(para, content)

    def _fill_summary_works_table(self, table, summary_data):
        """
        Table 11 — SUMMARY OF WORK DONE TO DATE (2 cols: Block | Description).
        Update existing rows where block matches. Append only truly NEW blocks.
        """
        # Build lookup of existing template rows by block name
        existing = {}
        for row in table.rows[1:]:
            key = row.cells[0].text.strip().upper()
            if key:
                existing[key] = row

        for component, description in summary_data.items():
            key = component.strip().upper()
            if key in existing:
                # Update existing row
                existing[key].cells[1].text = str(description)
            else:
                # Append a new row for blocks not in the template
                new_row = table.add_row()
                new_row.cells[0].text = component
                new_row.cells[1].text = str(description)
