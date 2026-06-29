import asyncio
import json
import os
import logging
import fitz  # PyMuPDF
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from ai_client import generate_structured_data
from schemas import DailyReportSchema, WeeklyReportSchema
import hashlib
import uuid
import re

logger = logging.getLogger(__name__)

class ReportParser:
    """
    Handles extraction with Fingerprinting and Caching.
    Ensures that identical files are never AI-scanned twice.
    """
    
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.daily_prompt = """
        Analyze this screenshot from a Daily Progress Report.
        
        1. Read the COVER PAGE first to identify the DATE and DAY of the week.
        2. READ section A (Contract Details) ONLY to extract 'Time Lapsed in Weeks', '% contract period elapsed', and '% work done'. SKIP sections B to D (Scope of Works).
        3. FOCUS ON: "SITE REPORT" through "SUMMARY OF WORKS DONE TO DATE".
        
        CRITICAL EXTRACTION RULES:
        - CONTRACT DETAILS: If you see section A, extract the numeric/percentage values for 'Time Lapsed in Weeks', '% contract period elapsed', and '% work done'. Map them to the keys: time_lapsed_weeks, pct_period_elapsed, pct_work_done.
        - WEATHER: Locate the 'WEATHER:' section in the SITE REPORT table. Extract the conditions for 'Morning', 'Afternoon', and 'Night' (map Night to 'evening' in the JSON schema).
        - LABOUR: Capture ALL labour categories listed in the table (e.g., Site Agent/PM, Ass. Site Agent, Office Attendant, Office Assistant, Foreman, Operator, Mason, Electrician, Painters, Carpenters, Steel fixers, Drivers, Surveyors, Intern, Unskilled, Safety officer, Store keeper, Security, etc).
          CRITICAL RULE: For every category visible in the table, return its value exactly as written (e.g. "4(m)", "13(12m,1f)", "41(7f,34m)"). 
          If a category row exists but has no value or shows a dash, return "0". NEVER return an empty string "" for any labour field.
          The TOTAL row at the bottom of the labour table MUST also be extracted and stored under the key "TOTAL".

        ╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
        ║   !!! CRITICAL WARNING: SECTION F and SECTION Q ARE COMPLETELY INDEPENDENT ENTITIES !!!         ║
        ║                                                                                                  ║
        ║   Their content must NEVER be placed in the other's JSON field — however similar they appear.   ║
        ║   Content of each section MUST remain in its own section and must NOT be copied to the other,   ║
        ║   regardless of what semantic similarity suggests. Treat them as two entirely separate documents.║
        ╚══════════════════════════════════════════════════════════════════════════════════════════════════╝

        SECTION F — "F. WORKS CARRIED OUT ON SITE"
          → Writes to JSON field: "building_works"
          → This page title starts with the letter "F." and describes ONLY what was physically done TODAY on site.
          → Example content: "Steel fixing to raft foundation", "Casting of blinding", "Fixing of formwork"
          → RULE: If the page title/header contains "Q." or "SUMMARY OF WORKS DONE TO DATE", set "building_works" to {{}} for that page. Do NOT read from it.

        SECTION Q — "Q. SUMMARY OF WORKS DONE TO DATE"  
          → Writes to JSON field: "summary_of_works"
          → This page title starts with the letter "Q." and lists CUMULATIVE work done since the start of the project, per block.
          → Example content: "BLOCK B1: Site clearance; Setting out; Mass excavation...", "SWIMMING POOL: None"
          → CRITICAL: Separate multiple activities with a semicolon ( ; ).
          → RULE: If the page title/header contains "F." or "WORKS CARRIED OUT ON SITE", set "summary_of_works" to {{}} for that page. Do NOT read from it.

        FINAL VERIFICATION: Before returning your JSON, ask yourself:
          - Does "building_works" contain ONLY today's activities from Section F? (No block-by-block cumulative lists)
          - Does "summary_of_works" contain ONLY the cumulative history from Section Q? (No today's tasks)
          If either answer is NO, correct your output before returning.
        ════════════════════════════════════════════════════════════════════════

        - SITE INSTRUCTIONS: Capture "REF. NO", "INSTRUCTION ISSUED", "DATE", and "INSTRUCTIONS GIVEN BY".
        - MACHINERY: Note the Quantity and Status (Working/Idle).
        - MATERIALS DELIVERED: Focus ONLY on Section 'G. MATERIALS DELIVERED TO SITE'. It has columns S/N, DESCRIPTION, QTY. Use lowercase keys: 'description', 'quantity', 'units'.
          CRITICAL RULE: Always extract 'quantity' as the numeric value ONLY (e.g. "689", "56.4", "913"). 
          Always extract 'units' as the unit of measure ONLY (e.g. "ft", "tons", "pcs", "bags", "tippers"). NEVER leave 'units' empty if a unit is visible in the table.

        - VISITORS: Locate the visitors section and extract the exact text verbatim (e.g. "2 visitors on site").
        - INTERNS: Locate the dedicated Intern/Interns section of the report (independent of the Labour table; it may be headed as 'INTERN', 'INTERNS', 'INTERN-SDHUD', 'INTERNS-SDHUD', or similar variations, case-insensitive). Extract the specific types of interns (e.g., 'TVETS', 'SDHUD') and their counts/names into the interns dictionary. Do NOT mix this with the Labour table.
        
        Return the data in perfect JSON matching this schema:
        - If the page DOES NOT contain ANY of the target sections (e.g. it's just a cover page or photos), return an empty object {{}} or null for all fields. 
        - Your response must be strictly valid JSON.
        - IGNORE any data that does not belong to the target month or year.
        {schema}
        """

        self.weekly_prompt = """
        Analyze this screenshot from a Weekly Progress Report.
        
        !!! CRITICAL DATE MAPPING RULE !!!
        1. Read the COVER PAGE to identify the REPORTING PERIOD (e.g. 13th - 19th April 2026).
           CRITICAL: IGNORE any dates found in 'Site Instructions' or 'Materials' tables when determining the year. ONLY use the Cover Page.
        2. Calculate the 7 dates for the week: Monday is the first date, Sunday is the last.
           - Example: "30th March - 5th April 2026" -> 
             * Monday 2026-03-30
             * Tuesday 2026-03-31
             * Wednesday 2026-04-01
             * ... etc.
        3. YOU MUST USE THIS EXACT FORMAT "YYYY-MM-DD" AS KEYS in 'labour_daily' and 'weather_daily'.
           - Example Key: "2026-03-30"
           - NEVER use "Mon", "Monday", or "Day YYYY-MM-DD". 
           - VERIFY THE YEAR: If the cover says 2026, all dates MUST be in 2026.
        !!! END OF CRITICAL RULE !!!

        1. READ section A (Contract Details/Project Info) ONLY to extract 'Time Lapsed in Weeks', '% contract period elapsed', and '% work done'. SKIP sections B to D.
        2. FOCUS ON the following sections: 
           - CONTRACT DETAILS: Extract 'Time Lapsed in Weeks', '% contract period elapsed', and '% work done' into the keys: time_lapsed_weeks, pct_period_elapsed, pct_work_done.
           - SITE REPORT: Progress details.
           - WORKS CARRIED OUT ON SITE: Day-by-day activities.
           - MATERIALS DELIVERED TO SITE: Extract description, quantity, and units.
           - LABOUR TURNOVER: Map Mon-Sun columns to the CORRECT "Day YYYY-MM-DD" dates.
             * EXHAUSTIVE: Capture EVERY row in the table (Site Agent, Foreman, Mason, Electrician, Steel fixers, Unskilled, Security, Interns, TOTAL, etc).
             * IMPORTANT: If the table spans multiple pages, extract every row visible on THIS page. Do not skip any rows.
             * Values exactly as written (e.g. "4(m)", "13(12m,1f)"). "0" for dash.
           - WEATHER: Map Mon-Sun to "Day YYYY-MM-DD" dates.
           - MACHINES AND EQUIPMENT: Name, qty, condition, status.
           - SITE INSTRUCTIONS: Ref No, Instruction, Date, Issued By.
           - SECURITY / HEALTH AND SAFETY: Verbatim prose and incident counts.
           - CHALLENGES / PENDING ISSUES: List of challenges.
           - Q. SUMMARY OF WORKS DONE TO DATE: List the cumulative history per block.
             * IMPORTANT: Separate each activity with a semicolon ( ; ).
             * Example: "Setting out; Casting of foundation; Columns to 1st floor"
        
        Return the data in perfect JSON matching this schema:
        {schema}
        """

    def _get_file_hash(self, file_path):
        """Generates a SHA256 fingerprint of the file's content."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _check_cache(self, pdf_path, report_type="DAILY"):
        """
        Quick cache-only check using SHA256 fingerprinting + report type.
        """
        file_hash = self._get_file_hash(pdf_path)
        # Use report_type in the cache name to prevent "Daily" scans from blocking "Weekly" scans of the same file
        cache_path = os.path.join(self.cache_dir, f"{report_type}_{file_hash}.json")
        if os.path.exists(cache_path):
            logger.info(f"🟢 RESUME: Found {report_type} cached results for {os.path.basename(pdf_path)}")
            with open(cache_path, "r") as f:
                return json.load(f)
        return None

    async def parse_report(self, pdf_path, session_dir, report_type="DAILY"):
        """Intelligently scans pages with per-page caching for resumption."""
        # Fast path: return from cache if this file was already fully processed
        cached = self._check_cache(pdf_path, report_type)
        if cached is not None:
            return cached

        file_hash = self._get_file_hash(pdf_path)
        cache_path = os.path.join(self.cache_dir, f"{report_type}_{file_hash}.json")
        page_cache_dir = os.path.join(self.cache_dir, f"pages_{report_type}_{file_hash[:8]}")
        os.makedirs(page_cache_dir, exist_ok=True)

        # Step 1: Integrity Check
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            logger.error(f"⚠️ Security/Integrity Error: {pdf_path} is not a valid PDF or is corrupted: {e}")
            return {"error": "Invalid or corrupted PDF file.", "status": "error"}

        # Step 2: Repair/Clean for better OCR
        try:
            temp_repair = os.path.join(session_dir, f"repaired_{uuid.uuid4().hex[:6]}.pdf")
            doc.save(temp_repair, clean=True, deflate=True)
            doc.close()
            doc = fitz.open(temp_repair)
        except Exception as repair_err:
            logger.warning(f"⚠️ PDF Repair failed, proceeding with original: {repair_err}")
            doc = fitz.open(pdf_path)
        
        screenshot_dir = os.path.join(session_dir, "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)

        print(f"Intelligent Scanning: {os.path.basename(pdf_path)}...")
        
        # SEARCHING_START for Weekly: Skip A-D and start at E regardless of title
        scanning_mode = "SEARCHING_START" if report_type == "WEEKLY" else "SEARCHING_SITE_REPORT"
        all_page_results = []
        reporting_context = "" 

        i = 0
        while i < len(doc):

            p_cache = os.path.join(page_cache_dir, f"page_{i}.json")
            if os.path.exists(p_cache):
                with open(p_cache, "r") as f:
                    res = json.load(f)
                    all_page_results.append(res)
                    # Sync context if this was the cover page
                    if i == 0 and report_type == "WEEKLY" and res.get("reporting_period"):
                        reporting_context = res["reporting_period"]
                    i += 1
                    continue

            text = doc[i].get_text().upper()
            
            # Cover Page is always processed for reporting period
            if i == 0: pass 
            elif scanning_mode == "SEARCHING_START":
                # Fallback: If text is missing (corrupted/scanned), use Vision to check for start
                if not text.strip():
                    logger.warning(f"⚠️ Page {i+1} has no extractable text. Using Vision Fallback.")
                    # We'll let it fall through to the screenshot logic below
                else:
                    has_start_header = any(
                        re.search(rf'^\s*{letter}[\.\s\:]', text, re.MULTILINE) 
                        for letter in ["A", "E", "F", "G"]
                    )
                    is_start_title = "SITE REPORT" in text or "WORKS CARRIED OUT" in text or "CONTRACT DETAILS" in text
                    
                    if has_start_header or is_start_title: 
                        scanning_mode = "EXTRACTING"
                    else:
                        i += 1
                        continue
            elif scanning_mode == "SEARCHING_SITE_REPORT":
                # Daily report logic fallback
                if not text.strip() and i < 5:
                    logger.warning(f"⚠️ Page {i+1} has no extractable text. Using Vision Fallback.")
                else:
                    is_site_report = "SITE REPORT" in text or "PROGRESS REPORT" in text or "CONTRACT DETAILS" in text
                    if is_site_report or i > 3: 
                        scanning_mode = "EXTRACTING"
                    else:
                        i += 1
                        continue
                
            trigger_skip = False
            if scanning_mode == "EXTRACTING":
                # End extraction at Sections like "R. PROGRESS PHOTOS" or "T. MATERIALS ON SITE"
                # We look for any Letter + Title at the start of a line to handle variability
                stop_pattern = r'^\s*[A-Z][\.\s\:]\s*(PROGRESS PHOTOS|MATERIALS ON SITE)'
                if i > 5 and re.search(stop_pattern, text, re.MULTILINE):
                    logger.info(f"🏁 End of extractable sections detected on Page {i+1}.")
                    trigger_skip = True

            print(f"   - Vision Scanning Page {i+1} of {len(doc)}...")
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) 
            tmp_path = os.path.join(screenshot_dir, f"page_{i+1}_{uuid.uuid4().hex[:6]}.png")
            pix.save(tmp_path)
            
            try:
                if report_type == "DAILY":
                    schema_json = DailyReportSchema.model_json_schema()
                    prompt = self.daily_prompt.format(schema=json.dumps(schema_json, indent=2))
                else:
                    schema_json = WeeklyReportSchema.model_json_schema()
                    prompt = self.weekly_prompt.format(schema=json.dumps(schema_json, indent=2))
                
                # Inject context if available to prevent hallucination on subsequent pages
                if reporting_context:
                    prompt = f"CONTEXT: The reporting period for this entire document is '{reporting_context}'. Use this period to strictly calculate ALL dates for 'YYYY-MM-DD' keys.\n\n" + prompt

                result = await generate_structured_data(prompt, tmp_path, mime_type="image/png")
                
                # Capture reporting period from page 1 to use as context for others
                if i == 0 and isinstance(result, dict) and result.get("reporting_period"):
                    reporting_context = result["reporting_period"]
                
                if isinstance(result, dict):
                    all_page_results.append(result)
                    with open(p_cache, "w") as f: json.dump(result, f)
                
            except Exception as e:
                logger.error(f"❌ Failed on Page {i+1}: {e}")
                raise 
            finally:
                if os.path.exists(tmp_path): os.remove(tmp_path)

            if trigger_skip:
                scanning_mode = "SEARCHING_SIGNATURE"

            if scanning_mode == "SEARCHING_SIGNATURE":
                found_signature = False
                for j in range(i + 1, len(doc)):
                    if "PREPARED BY" in doc[j].get_text().upper():
                        i = j - 1
                        found_signature = True
                        break
                if not found_signature:
                    break 

            i += 1

        # Final Merge
        if report_type == "DAILY":
            final_data = self._merge_results(all_page_results)
            # --- MANUAL OVERRIDE FOR DAILY REPORTS ---
            # AI frequently hallucinates numbers in tables; we override with precise PyMuPDF extraction
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
        """
        Manually extracts Labour and Materials tables from the PDF to avoid AI hallucinations.
        Uses fitz's find_tables() for high-fidelity structural extraction.
        """
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
                    
                # Normalize headers for identification
                headers = [str(h).upper().strip() if h else "" for h in data[0]]
                
                # 1. LABOUR TURNOVER Identification
                is_labour = any("LABOUR" in h or "CATEGORY" in h for h in headers)
                if not is_labour and data:
                    # Fallback: check the first row of actual data for the keyword
                    is_labour = any("CATEGORY" in str(c).upper() for c in data[0])

                if is_labour:
                    for row in data[1:]:
                        if not row or not row[0]: continue
                        cat = str(row[0]).strip()
                        if not cat: continue
                        
                        # Handle variable data columns (e.g., Day, Night)
                        if len(row) == 2:
                            # Standard 2-column format (Category, Value)
                            val = str(row[1]).strip() if row[1] else "0"
                        elif len(row) >= 3:
                            # Multi-column format (e.g., Category, Day, Night)
                            # Store as a sub-dict mapping header name to value
                            val_dict = {}
                            for i in range(1, len(row)):
                                h_name = headers[i] if i < len(headers) else f"Col_{i}"
                                # Clean up common variations like "No.-Day" or "No-Day" to "Day"
                                h_norm = h_name.replace("NO.-", "").replace("NO-", "").capitalize()
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
                        
                        # Split numeric quantity from units (e.g. "29.60 tons" -> "29.60", "tons")
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


    def _extract_images(self, pdf_path, session_dir):
        img_dir = os.path.join(session_dir, "extracted_images")
        os.makedirs(img_dir, exist_ok=True)
        doc = fitz.open(pdf_path)
        saved_paths = []
        for i in range(len(doc)):
            for img_index, img in enumerate(doc.get_page_images(i)):
                xref = img[0]
                base_image = doc.extract_image(xref)
                img_path = os.path.join(img_dir, f"p{i+1}_img{img_index}.png")
                with open(img_path, "wb") as f:
                    f.write(base_image["image"])
                saved_paths.append(img_path)
        return saved_paths

    def _merge_results(self, page_results):
        """Intelligently merges data from multiple pages into one DailyReport."""
        merged = {
            "date": "", "day_of_week": "", 
            "time_lapsed_weeks": "", "pct_period_elapsed": "", "pct_work_done": "",
            "weather": {},
            "labour": {}, "building_works": {}, "general_works": [],
            "machinery": [], "materials_delivered": [], "material_tests": [],
            "instructions": [], "interns": {}, "security_status": "",
            "health_safety_status": "", "visitors": [], "challenges": [],
            "summary_of_works": {}
        }
        for res in page_results:
            if not isinstance(res, dict): continue
            for field in ["date", "day_of_week", "security_status", "health_safety_status", "time_lapsed_weeks", "pct_period_elapsed", "pct_work_done"]:
                if res.get(field) and not merged[field]:
                    merged[field] = res[field]
            if res.get("weather"): 
                for k, v in res["weather"].items():
                    if v and v != "-":
                        merged["weather"][k] = v
            if res.get("labour"): merged["labour"].update(res["labour"])
            if res.get("building_works"): merged["building_works"].update(res["building_works"])
            if res.get("summary_of_works"): merged["summary_of_works"].update(res["summary_of_works"])
            if res.get("interns"): merged["interns"].update(res["interns"])
            if res.get("general_works"): merged["general_works"].extend(res["general_works"])
            if res.get("machinery"): merged["machinery"].extend(res["machinery"])
            if res.get("materials_delivered"): merged["materials_delivered"].extend(res["materials_delivered"])
            if res.get("material_tests"): merged["material_tests"].extend(res["material_tests"])
            if res.get("instructions"): merged["instructions"].extend(res["instructions"])
            if res.get("visitors"): merged["visitors"].extend(res["visitors"])
            if res.get("challenges"): merged["challenges"].extend(res["challenges"])
        
        # Default date fallback for instructions
        report_date = merged.get("date", "Unknown Date")
        for inst in merged.get("instructions", []):
            if isinstance(inst, dict) and not inst.get("date"):
                inst["date"] = report_date
                
        return merged

    def _merge_weekly_results(self, page_results):
        """Intelligently merges data from multiple pages into one WeeklyReport."""
        merged = {
            "reporting_period": "",
            "time_lapsed_weeks": "", "pct_period_elapsed": "", "pct_work_done": "",
            "labour_daily": {}, "weather_daily": {},
            "insurances": [], "materials_delivered": [], "machinery": [],
            "instructions": [], "security_prose": "", "health_safety_prose": "",
            "visitors_prose": "", "challenges_prose": "", "summary_to_date": {}
        }
        for res in page_results:
            if not isinstance(res, dict): continue
            
            # 1. Period & Contract Metadata
            if res.get("reporting_period") and not merged["reporting_period"]:
                merged["reporting_period"] = res["reporting_period"]
            
            for field in ["time_lapsed_weeks", "pct_period_elapsed", "pct_work_done"]:
                if res.get(field) and not merged[field]:
                    merged[field] = res[field]
            
            # 2. Prose Sections (Concatenate if they span pages)
            for field in ["security_prose", "health_safety_prose", "visitors_prose", "challenges_prose"]:
                if res.get(field):
                    val = res[field].strip()
                    if not val: continue
                    if merged[field]:
                        if val not in merged[field]:
                            merged[field] = merged[field].rstrip(".") + ". " + val
                    else:
                        merged[field] = val

            # 3. Labour
            if res.get("labour_daily"): 
                for d, cats in res["labour_daily"].items():
                    if d not in merged["labour_daily"]: 
                        merged["labour_daily"][d] = {}
                    for cat, val in cats.items():
                        curr = merged["labour_daily"][d].get(cat, "0")
                        if val and val != "0" and val != "":
                            merged["labour_daily"][d][cat] = val
                        elif curr == "0" or curr == "":
                            merged["labour_daily"][d][cat] = val

            if res.get("weather_daily"):
                for d, winfo in res["weather_daily"].items():
                    if d not in merged["weather_daily"]: 
                        merged["weather_daily"][d] = {}
                    if isinstance(winfo, dict):
                        for field, val in winfo.items():
                            if val and val != "-" and val != "":
                                merged["weather_daily"][d][field] = val
                    elif isinstance(winfo, str) and winfo.strip() and winfo != "-":
                        # If AI returned a single string for the whole day
                        merged["weather_daily"][d]["condition"] = winfo
            
            # 4. Summary to Date (Section Q - Concatenate block descriptions if split)
            if res.get("summary_to_date"):
                for block, desc in res["summary_to_date"].items():
                    if not desc: continue
                    if block in merged["summary_to_date"]:
                        existing = merged["summary_to_date"][block]
                        if desc not in existing:
                            merged["summary_to_date"][block] = existing.rstrip(".") + "; " + desc
                    else:
                        merged["summary_to_date"][block] = desc

            if res.get("insurances"): merged["insurances"].extend(res["insurances"])
            if res.get("materials_delivered"): merged["materials_delivered"].extend(res["materials_delivered"])
            if res.get("machinery"): merged["machinery"].extend(res["machinery"])
            if res.get("instructions"): merged["instructions"].extend(res["instructions"])
        return merged

    def _manual_extract_weekly_tables(self, doc):
        """
        Targeted extraction of Labour and Materials from Weekly Reports.
        Supports multi-page tables and split rows (where a cell spans two pages).
        """
        labour_data = {}
        materials_data = []
        days_of_week = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        
        last_labour_cat = None # Track for split-row merging

        for page_idx, page in enumerate(doc):
            tables = page.find_tables()
            for table in tables:
                raw_rows = table.extract()
                if not raw_rows: continue
                headers = [str(c).strip().upper() for c in raw_rows[0] if c]
                
                # --- 1. Labour Matrix Detection & Continuation ---
                is_labour = any("CATEGORY" in h for h in headers) and any(d in "".join(headers) for d in days_of_week)
                is_continuation = len(raw_rows[0]) == 8 and last_labour_cat is not None and not is_labour
                
                if is_labour or is_continuation:
                    day_indices = {i: i for i in range(1, 8)} # Default for headerless
                    if is_labour:
                        day_indices = {}
                        for i, h in enumerate(headers):
                            for d_idx, d_name in enumerate(days_of_week):
                                if d_name in h: day_indices[d_idx] = i
                    
                    start_row = 1 if is_labour else 0
                    for row in raw_rows[start_row:]:
                        if len(row) < 8: continue
                        cat = str(row[0] or "").strip()
                        
                        # Handle Split Row: If first cell is empty, it's a continuation of the previous row
                        if not cat and last_labour_cat:
                            for d_idx in range(7):
                                col_idx = day_indices.get(d_idx+1 if is_continuation else d_idx)
                                if col_idx and col_idx < len(row):
                                    val = str(row[col_idx] or "").strip()
                                    if val:
                                        # Merge strings: e.g., "2(1m," + "1f)" -> "2(1m, 1f)"
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

                # --- 2. Materials Table Detection ---
                has_desc = any("DESCRIPTION" in h for h in headers)
                has_qty = any("QUANTITY" in h for h in headers)
                
                if has_desc and has_qty:
                    idx_desc = next((i for i, h in enumerate(headers) if "DESCRIPTION" in h), -1)
                    idx_qty = next((i for i, h in enumerate(headers) if "QUANTITY" in h), -1)
                    
                    if idx_desc != -1 and idx_qty != -1:
                        for row in raw_rows[1:]:
                            if len(row) > max(idx_desc, idx_qty):
                                desc = str(row[idx_desc]).strip()
                                if not desc or desc.upper() in ["DESCRIPTION", "TOTAL QUANTITY", "QUANTITY", "S/NO", "S/N"]:
                                    continue
                                materials_data.append({
                                    "description": desc,
                                    "quantity": str(row[idx_qty]).strip()
                                })

        return labour_data, materials_data

    def _parse_weekly_start_date(self, period_str):
        """
        Parses '13TH - 19TH APRIL 2026' into a datetime object for the Monday.
        Handles variations like 'MARCH AND APRIL'.
        """
        import re
        from datetime import datetime, timedelta
        
        try:
            year_match = re.search(r"(\d{4})", period_str)
            year = int(year_match.group(1)) if year_match else datetime.now().year
            months = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", 
                      "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]
            found_months = [m for m in months if m in period_str.upper()]
            if not found_months: return None
            
            month_name = found_months[-1]
            month_idx = months.index(month_name) + 1
            day_match = re.search(r"(\d{1,2})", period_str)
            if not day_match: return None
            day = int(day_match.group(1))
            
            if len(found_months) > 1 and day > 20:
                month_idx = months.index(found_months[0]) + 1
            
            start_dt = datetime(year, month_idx, day)
            if start_dt.weekday() != 0:
                # 0 is Monday. We log this as INFO as it might be a partial week (e.g. start of month).
                original_dt = start_dt
                start_dt = start_dt - timedelta(days=start_dt.weekday())
                logger.info(f"📅 Note: Weekly period '{period_str}' starts on a {original_dt.strftime('%A')} ({original_dt.strftime('%Y-%m-%d')}). Normalized to preceding Monday: {start_dt.strftime('%Y-%m-%d')}.")
            return start_dt
        except Exception as e:
            logger.error(f"❌ Failed to parse weekly start date from '{period_str}': {e}")
            return None
