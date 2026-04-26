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
        - LABOUR: Capture categories (e.g. Mason, Steel Fixer). If a report shows 'Day' and 'Night' shifts, capture them separately (e.g., {{"Mason": {{"Day": "5", "Night": "2"}}}}).
        - SITE INSTRUCTIONS: Capture "REF. NO", "INSTRUCTION ISSUED", "DATE", and "INSTRUCTIONS GIVEN BY".
        - WEATHER: Locate the 'WEATHER:' label. It is a 2-column table with periods (Morning, Afternoon, Night) in the first column and the condition (e.g. 'Sunny', 'Cloudy') in the second column. Map 'Night' to 'evening'. Extract the exact condition text for "morning", "afternoon", and "evening".
        - MACHINERY: Note the Quantity and Status (Working/Idle).
        - MATERIALS DELIVERED: Capture "Description", "Quantity", and "Units".
        - SUMMARY OF WORKS: Capture the 'Summary to Date' text for each component/block.
        - INTERNS & VISITORS: Extract the specific values and names.
        - SKIP: "Progress Photos" and "Materials on Site" sections.
        
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

    async def parse_report(self, pdf_path, session_dir, report_type="DAILY"):
        # 1. Check for 'Resume' using Fingerprinting
        file_hash = self._get_file_hash(pdf_path)
        cache_path = os.path.join(self.cache_dir, f"{file_hash}.json")
        
        if os.path.exists(cache_path):
            logger.info(f"🟢 RESUME: Found cached results for {os.path.basename(pdf_path)} (Hash: {file_hash[:8]})")
            with open(cache_path, "r") as f:
                return json.load(f)

    async def parse_report(self, pdf_path, session_dir, report_type="DAILY"):
        """Intelligently scans pages with per-page caching for resumption."""
        file_hash = self._get_file_hash(pdf_path)
        cache_path = os.path.join(self.cache_dir, f"{file_hash}.json")
        page_cache_dir = os.path.join(self.cache_dir, f"pages_{file_hash[:8]}")
        os.makedirs(page_cache_dir, exist_ok=True)
        
        if os.path.exists(cache_path):
            logger.info(f"🟢 CACHE HIT: {os.path.basename(pdf_path)}")
            with open(cache_path, "r") as f: return json.load(f)

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
                    # Update state based on cached result
                    if res.get("summary_of_works") and i > 2: scanning_mode = "SEARCHING_SIGNATURE"
                    i += 1
                    continue

            # Always scan Page 1 (Cover)
            if i == 0: pass 
            elif scanning_mode == "SEARCHING_SITE_REPORT":
                text = doc[i].get_text().upper()
                if "SITE REPORT" not in text: 
                    i += 1
                    continue
                scanning_mode = "EXTRACTING"

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
                    
                    if result.get("summary_of_works") and i > 2:
                        logger.info("🏁 Summary detected. Skipping to signature...")
                        scanning_mode = "SEARCHING_SIGNATURE"
                
                await asyncio.sleep(4) 
            except Exception as e:
                logger.error(f"❌ Failed on Page {i+1}: {e}")
                raise # Re-raise to let the user know we stopped
            finally:
                if os.path.exists(tmp_path): os.remove(tmp_path)

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
            if res.get("weather"): merged["weather"].update(res["weather"])
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
