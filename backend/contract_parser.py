import fitz
import json
import os
import logging
from ai_client import generate_structured_data
from schemas import ContractSummarySchema

logger = logging.getLogger(__name__)

class ContractParser:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.contract_file = os.path.join(self.cache_dir, "contract_summary.json")

    async def extract_contract_details(self, pdf_path):
        """
        Scans only the first few pages (Cover + Sections A-D) to get project context.
        """
        doc = fitz.open(pdf_path)
        # We only need the first 4-5 pages for project details
        pages_to_scan = min(5, len(doc))
        
        combined_text = ""
        for i in range(pages_to_scan):
            combined_text += f"\n--- PAGE {i+1} ---\n"
            combined_text += doc[i].get_text()

        prompt = """
        Analyze the first few pages of this Construction Progress Report and extract the permanent CONTRACT DETAILS.
        
        Look for:
        1. Project Title / Name
        2. Contract Number
        3. Employer (Client)
        4. Contractor
        5. Consultant / Project Manager
        6. Contract Sum (Price)
        7. Contract Period (Duration)
        8. Date of Possession
        9. Date of Commencement
        10. Expected Completion Date
        11. Scope of Works (List the main components mentioned in Sections A-D)
        12. Project Location
        
        Return the data in valid JSON matching this schema:
        {schema}
        """
        
        # For simplicity, we'll take a screenshot of the first page (cover) as well for better visual recognition
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        screenshot_path = "temp_contract_cover.png"
        pix.save(screenshot_path)
        
        schema_json = ContractSummarySchema.model_json_schema()
        full_prompt = prompt.format(schema=json.dumps(schema_json, indent=2))
        
        try:
            result = await generate_structured_data(full_prompt, screenshot_path, mime_type="image/png")
            if isinstance(result, dict):
                # Save to permanent storage
                with open(self.contract_file, "w") as f:
                    json.dump(result, f, indent=2)
                return result
        finally:
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            doc.close()
            
        return None

    def get_contract_summary(self):
        if os.path.exists(self.contract_file):
            with open(self.contract_file, "r") as f:
                return json.load(f)
        return None
