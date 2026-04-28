import asyncio
import json
import os
import logging
import fitz  # PyMuPDF
from ai_client import generate_structured_data
from schemas import DailyReportSchema
import hashlib
import uuid

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
          → Example content: "BLOCK B1: Site clearance, Setting out, Mass excavation...", "SWIMMING POOL: None"
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

        doc = fitz.open(pdf_path)
        screenshot_dir = os.path.join(session_dir, "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)

        print(f"Intelligent Scanning: {os.path.basename(pdf_path)}...")
        
        # NAVIGATION STATE
        scanning_mode = "SEARCHING_SITE_REPORT"
        all_page_results = []

        i = 0
        while i < len(doc):
            # RESUMPTION CHECK: Check if this page is already in the page_cache
            p_cache = os.path.join(page_cache_dir, f"page_{i}.json")
            if os.path.exists(p_cache):
                with open(p_cache, "r") as f:
                    res = json.load(f)
                    all_page_results.append(res)
                    # Update state based on cached result (no longer skipping based on summary)
                    i += 1
                    continue

            text = doc[i].get_text().upper()
            
            # Always scan Page 1 (Cover)
            if i == 0: pass 
            elif scanning_mode == "SEARCHING_SITE_REPORT":
                if "SITE REPORT" not in text: 
                    i += 1
                    continue
                scanning_mode = "EXTRACTING"
                
            trigger_skip = False
            if scanning_mode == "EXTRACTING":
                # We do not want to trigger on the Table of Contents page (Page 1 or 2)
                if i > 1 and "PROGRESS PHOTOS" in text:
                    logger.info("🏁 End of extractable sections detected on this page. Will skip after scanning it.")
                    trigger_skip = True

            print(f"   - Vision Scanning Page {i+1} of {len(doc)}...")
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) 
            tmp_path = os.path.join(screenshot_dir, f"page_{i+1}_{uuid.uuid4().hex[:6]}.png")
            pix.save(tmp_path)
            
            try:
                schema_json = DailyReportSchema.model_json_schema()
                prompt = self.daily_prompt.format(schema=json.dumps(schema_json, indent=2))
                result = await generate_structured_data(prompt, tmp_path, mime_type="image/png")
                
                if isinstance(result, dict):
                    all_page_results.append(result)
                    # SAVE PER-PAGE CACHE
                    with open(p_cache, "w") as f: json.dump(result, f)
                    
                    pass # We now rely on text search to skip to signature
                
                await asyncio.sleep(4) 
            except Exception as e:
                logger.error(f"❌ Failed on Page {i+1}: {e}")
                raise # Re-raise to let the user know we stopped
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
                    break # Reached the end or didn't find it, so exit the while loop

            i += 1

        # Final Merge
        final_data = self._merge_results(all_page_results)
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
            
            # 1. Direct fields (Take the first non-empty value)
            for field in ["date", "day_of_week", "security_status", "health_safety_status"]:
                if res.get(field) and not merged[field]:
                    merged[field] = res[field]
            
            # 2. Dictionary fields (Update/Combine)
            if res.get("weather"): 
                for k, v in res["weather"].items():
                    if v and v != "-":
                        merged["weather"][k] = v
            if res.get("labour"): merged["labour"].update(res["labour"])
            if res.get("building_works"): merged["building_works"].update(res["building_works"])
            if res.get("summary_of_works"): merged["summary_of_works"].update(res["summary_of_works"])
            if res.get("interns"): merged["interns"].update(res["interns"])
            
            # 3. List fields (Extend/Append)
            if res.get("general_works"): merged["general_works"].extend(res["general_works"])
            if res.get("machinery"): merged["machinery"].extend(res["machinery"])
            if res.get("materials_delivered"): merged["materials_delivered"].extend(res["materials_delivered"])
            if res.get("material_tests"): merged["material_tests"].extend(res["material_tests"])
            if res.get("instructions"): merged["instructions"].extend(res["instructions"])
            if res.get("visitors"): merged["visitors"].extend(res["visitors"])
            if res.get("challenges"): merged["challenges"].extend(res["challenges"])

        return merged
