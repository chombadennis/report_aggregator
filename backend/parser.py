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
        Analyze this screenshot of a Daily Progress Report.
        Extract the information into perfect JSON.
        
        CRITICAL: 
        1. Identify the WORK ZONES (Blocks) and their tasks.
        2. Identify ALL MATERIAL TESTS (e.g. Slump, Cube, Compaction).
           Capture the type, details, and location.
        
        Schema: {schema}
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

        # 2. Not in Cache? Start Vision Scan
        doc = fitz.open(pdf_path)
        aggregated_data = {
            "building_works": {},
            "labour": {},
            "weather": {},
            "material_tests": [],
            "image_paths": [],
            "fingerprint": file_hash # Store for integrity
        }

        schema_json = DailyReportSchema.model_json_schema()
        prompt = self.daily_prompt.format(schema=json.dumps(schema_json, indent=2))
        screenshot_dir = os.path.join(session_dir, "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)

        for i in range(len(doc)):
            print(f"   - Vision Scanning Page {i+1} of {len(doc)}...")
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) 
            tmp_path = os.path.join(screenshot_dir, f"page_{i+1}_{uuid.uuid4().hex[:6]}.png")
            pix.save(tmp_path)
            
            try:
                result = await generate_structured_data(prompt, tmp_path, mime_type="image/png")
                
                # --- CONFIDENCE CHECK & DEEP SCAN FALLBACK ---
                conf = result.get("confidence_score", 1.0)
                if conf < 0.85:
                    logger.warning(f"⚠️ Low Confidence ({conf}) on Page {i+1}. Triggering Deep Scan with Gemini Pro...")
                    result = await generate_structured_data(prompt, tmp_path, mime_type="image/png", force_pro=True)

                if isinstance(result, dict):
                    if "building_works" in result: aggregated_data["building_works"].update(result["building_works"])
                    if "labour" in result: aggregated_data["labour"].update(result["labour"])
                    if "weather" in result: aggregated_data["weather"].update(result["weather"])
                    if "material_tests" in result: aggregated_data["material_tests"].extend(result["material_tests"])
                await asyncio.sleep(2) 
            finally:
                if os.path.exists(tmp_path): os.remove(tmp_path)

        # 3. Extract site photos
        aggregated_data["image_paths"] = self._extract_images(pdf_path, session_dir)

        # 4. SAVE to Cache for future Resumes
        with open(cache_path, "w") as f:
            json.dump(aggregated_data, f, indent=2)
            logger.info(f"🎯 CACHED: Saved results for fingerprint {file_hash[:8]}")

        return aggregated_data

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
