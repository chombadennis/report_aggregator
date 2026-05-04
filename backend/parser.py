import asyncio
import json
import os
import logging
import fitz  # PyMuPDF
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
        2. SKIP sections A to D (Scope of Works) - these are repetitive.
        3. FOCUS ON: "SITE REPORT" through "SUMMARY OF WORKS DONE TO DATE".
        
        CRITICAL EXTRACTION RULES:
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
        - INTERNS: Extract the specific values and names.
        
        Return the data in perfect JSON matching this schema:
        - If the page DOES NOT contain ANY of the target sections (e.g. it's just a cover page or photos), return an empty object {} or null for all fields. 
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
        3. YOU MUST USE THIS EXACT FORMAT "Day YYYY-MM-DD" AS KEYS in 'labour_daily' and 'weather_daily'.
           - Example Key: "Monday 2026-03-30"
           - NEVER use "Mon", "Monday", or just the date. 
           - VERIFY THE YEAR: If the cover says 2026, all dates MUST be in 2026.
        !!! END OF CRITICAL RULE !!!

        1. SKIP sections A to D (Project Info, Scope of Works).
        2. FOCUS ON the following sections: 
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

    def _check_cache(self, pdf_path):
        """
        Quick cache-only check using SHA256 fingerprinting.
        Returns cached data immediately if available, otherwise returns None.
        Use this for a fast pre-flight check before committing to a full scan.
        """
        file_hash = self._get_file_hash(pdf_path)
        cache_path = os.path.join(self.cache_dir, f"{file_hash}.json")
        if os.path.exists(cache_path):
            logger.info(f"🟢 RESUME: Found cached results for {os.path.basename(pdf_path)} (Hash: {file_hash[:8]})")
            with open(cache_path, "r") as f:
                return json.load(f)
        return None

    async def parse_report(self, pdf_path, session_dir, report_type="DAILY"):
        """Intelligently scans pages with per-page caching for resumption."""
        # Fast path: return from cache if this file was already fully processed
        cached = self._check_cache(pdf_path)
        if cached is not None:
            return cached

        file_hash = self._get_file_hash(pdf_path)
        cache_path = os.path.join(self.cache_dir, f"{file_hash}.json")
        page_cache_dir = os.path.join(self.cache_dir, f"pages_{file_hash[:8]}")
        os.makedirs(page_cache_dir, exist_ok=True)

        # Unconditionally repair/clean PDF to fix zlib stream errors and improve OCR accuracy
        try:
            doc = fitz.open(pdf_path)
            temp_repair = os.path.join(session_dir, f"repaired_{uuid.uuid4().hex[:6]}.pdf")
            doc.save(temp_repair, clean=True, deflate=True)
            doc.close()
            doc = fitz.open(temp_repair)
        except Exception as repair_err:
            logger.warning(f"⚠️ PDF Repair failed, attempting normal open: {repair_err}")
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
                        for letter in ["E", "F", "G"]
                    )
                    is_start_title = "SITE REPORT" in text or "WORKS CARRIED OUT" in text
                    
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
                    is_site_report = "SITE REPORT" in text or "PROGRESS REPORT" in text
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
                    prompt = f"CONTEXT: The reporting period for this entire document is '{reporting_context}'. Use this period to strictly calculate ALL dates for 'Day YYYY-MM-DD' keys.\n\n" + prompt

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
        else:
            final_data = self._merge_weekly_results(all_page_results)
            
        final_data["fingerprint"] = file_hash
        with open(cache_path, "w") as f: json.dump(final_data, f, indent=2)
        return final_data


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
            "date": "", "day_of_week": "", "weather": {},
            "labour": {}, "building_works": {}, "general_works": [],
            "machinery": [], "materials_delivered": [], "material_tests": [],
            "instructions": [], "interns": {}, "security_status": "",
            "health_safety_status": "", "visitors": [], "challenges": [],
            "summary_of_works": {}
        }
        for res in page_results:
            if not isinstance(res, dict): continue
            for field in ["date", "day_of_week", "security_status", "health_safety_status"]:
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
        return merged

    def _merge_weekly_results(self, page_results):
        """Intelligently merges data from multiple pages into one WeeklyReport."""
        merged = {
            "reporting_period": "",
            "labour_daily": {}, "weather_daily": {},
            "insurances": [], "materials_delivered": [], "machinery": [],
            "instructions": [], "security_prose": "", "health_safety_prose": "",
            "visitors_prose": "", "challenges_prose": "", "summary_to_date": {}
        }
        for res in page_results:
            if not isinstance(res, dict): continue
            
            # 1. Period
            if res.get("reporting_period") and not merged["reporting_period"]:
                merged["reporting_period"] = res["reporting_period"]
            
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
                        # Only update if current value is empty or "0"
                        curr = merged["labour_daily"][d].get(cat, "0")
                        if val and val != "0" and val != "":
                            merged["labour_daily"][d][cat] = val
                        elif curr == "0" or curr == "":
                            merged["labour_daily"][d][cat] = val

            if res.get("weather_daily"):
                for d, winfo in res["weather_daily"].items():
                    if d not in merged["weather_daily"]: 
                        merged["weather_daily"][d] = {}
                    for field, val in winfo.items():
                        if val and val != "-" and val != "":
                            merged["weather_daily"][d][field] = val
            
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
