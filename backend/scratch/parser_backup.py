import json
import os
import hashlib
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import fitz  # PyMuPDF

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("parser")

class ReportParser:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def parse_report(self, pdf_path: str, session_dir: str, report_type: str = "DAILY") -> Dict[str, Any]:
        """Parses a single PDF report using AI Vision and Manual Overrides."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Check Cache
        with open(pdf_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()[:32]
        
        cache_filename = f"{file_hash}.json"
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        if os.path.exists(cache_path):
            with open(cache_path, "r") as f:
                logger.info(f"🟢 RESUME: Found cached results for {os.path.basename(pdf_path)}")
                return json.load(f)

        logger.info(f"Intelligent Scanning: {os.path.basename(pdf_path)}...")
        doc = fitz.open(pdf_path)
        
        # 1. AI Vision Scanning (Simulated for this script, normally calls AIClient)
        # In the real app, this part is already implemented.
        all_page_results = [] # In real app, this is populated via AI scanning
        
        # Final Merge
        if report_type == "DAILY":
            final_data = self._merge_results(all_page_results)
            # --- MANUAL OVERRIDE FOR DAILY REPORTS ---
            try:
                m_labour, m_materials = self._manual_extract_daily_tables(doc)
                if m_labour:
                    logger.info(f"🛠️ Manual Labour Override: {len(m_labour)} categories found.")
                    final_data["labour"] = m_labour
                if m_materials:
                    logger.info(f"🛠️ Manual Materials Override: {len(m_materials)} items found.")
                    final_data["materials_delivered"] = m_materials
            except Exception as me:
                logger.warning(f"⚠️ Manual table extraction failed: {me}")
        else:
            final_data = self._merge_weekly_results(all_page_results)
            # --- MANUAL OVERRIDE FOR WEEKLY REPORTS ---
            try:
                m_labour, m_materials = self._manual_extract_weekly_tables(doc)
                
                # 1. Map Labour Matrix to Dates
                if m_labour and final_data.get("reporting_period"):
                    period_str = final_data["reporting_period"]
                    start_date = self._parse_weekly_start_date(period_str)
                    if start_date:
                        clean_labour_daily = {}
                        for i in range(7):
                            day_dt = start_date + timedelta(days=i)
                            date_str = day_dt.strftime("%Y-%m-%d")
                            clean_labour_daily[date_str] = {
                                cat: vals[i] for cat, vals in m_labour.items()
                            }
                        logger.info(f"🛠️ Manual Weekly Labour Override: {len(m_labour)} categories mapped.")
                        final_data["labour_daily"] = clean_labour_daily
                
                # 2. Materials Override
                if m_materials:
                    logger.info(f"🛠️ Manual Weekly Materials Override: {len(m_materials)} items found.")
                    final_data["materials_delivered"] = m_materials

            except Exception as me:
                logger.warning(f"⚠️ Manual weekly table extraction failed: {me}")
            
        final_data["fingerprint"] = file_hash
        with open(cache_path, "w") as f: json.dump(final_data, f, indent=2)
        return final_data

    def _manual_extract_daily_tables(self, doc):
        """Standard daily extraction."""
        labour_data = {}
        materials_data = []
        for page in doc:
            tabs = page.find_tables()
            for tab in tabs:
                data = tab.extract()
                if not data or len(data) < 2: continue
                headers = [str(c).strip().upper() for c in data[0] if c]
                if any(k in "".join(headers) for k in ["LABOUR", "CATEGORY"]):
                    for row in data[1:]:
                        if row and row[0]: labour_data[row[0].strip()] = row[1].strip() if len(row)>1 else "0"
                if any("DESCRIPTION" in h for h in headers) and any("QUANTITY" in h for h in headers):
                    for row in data[1:]:
                        if row and len(row)>1: materials_data.append({"description": row[0], "quantity": row[1]})
        return labour_data, materials_data

    def _manual_extract_weekly_tables(self, doc):
        """
        Targeted extraction of Labour and Materials from Weekly Reports.
        """
        labour_data = {}
        materials_data = []
        days_of_week = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

        for page in doc:
            text = page.get_text().upper()
            
            # 1. Labour Matrix
            if "LABOUR" in text and "CATEGORY" in text:
                for table in page.find_tables():
                    headers = [str(c).strip().upper() for c in table.extract()[0] if c]
                    if any("CATEGORY" in h for h in headers) and any(d in "".join(headers) for d in days_of_week):
                        raw_rows = table.extract()
                        day_indices = {}
                        for i, h in enumerate(headers):
                            for d_idx, d_name in enumerate(days_of_week):
                                if d_name in h: day_indices[d_idx] = i
                        for row in raw_rows[1:]:
                            if not row or not row[0]: continue
                            cat = str(row[0]).strip()
                            if not cat or cat.upper() in ["CATEGORY", "TOTAL", "SUB-TOTAL"]: continue
                            if cat not in labour_data: labour_data[cat] = ["0"] * 7
                            for d_idx, col_idx in day_indices.items():
                                if col_idx < len(row): labour_data[cat][d_idx] = str(row[col_idx]).strip() or "0"
                        break

            # 2. Materials Table
            if "MATERIALS DELIVERED" in text:
                for table in page.find_tables():
                    headers = [str(c).strip().upper() for c in table.extract()[0] if c]
                    if any("DESCRIPTION" in h for h in headers) and any("QUANTITY" in h for h in headers):
                        raw_rows = table.extract()
                        idx_desc = next((i for i, h in enumerate(headers) if "DESCRIPTION" in h), -1)
                        idx_qty = next((i for i, h in enumerate(headers) if "QUANTITY" in h), -1)
                        if idx_desc != -1 and idx_qty != -1:
                            for row in raw_rows[1:]:
                                if len(row) > max(idx_desc, idx_qty):
                                    desc = str(row[idx_desc]).strip()
                                    if desc and desc.upper() not in ["DESCRIPTION", "TOTAL QUANTITY", "QUANTITY"]:
                                        materials_data.append({"description": desc, "quantity": str(row[idx_qty]).strip()})
                        break
        return labour_data, materials_data

    def _parse_weekly_start_date(self, period_str):
        """Parses start date from weekly period string."""
        try:
            year_match = re.search(r"(\d{4})", period_str)
            year = int(year_match.group(1)) if year_match else datetime.now().year
            months = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]
            found_months = [m for m in months if m in period_str.upper()]
            if not found_months: return None
            month_idx = months.index(found_months[-1]) + 1
            day_match = re.search(r"(\d{1,2})", period_str)
            if not day_match: return None
            day = int(day_match.group(1))
            if len(found_months) > 1 and day > 20: month_idx = months.index(found_months[0]) + 1
            return datetime(year, month_idx, day)
        except: return None

    def _merge_results(self, page_results):
        merged = {"date": "", "labour": {}, "materials_delivered": [], "instructions": []}
        # In real app, this is much more complex
        return merged

    def _merge_weekly_results(self, page_results):
        merged = {"reporting_period": "", "labour_daily": {}, "materials_delivered": [], "instructions": []}
        # In real app, this is much more complex
        for res in page_results:
            if res.get("reporting_period"): merged["reporting_period"] = res["reporting_period"]
        return merged
