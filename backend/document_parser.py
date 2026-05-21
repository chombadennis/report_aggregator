import fitz
import json
import os
import logging
from ai_client import generate_structured_data

logger = logging.getLogger(__name__)

class DocumentParser:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        self.docs_dir = os.path.join(self.cache_dir, "project_documents")
        os.makedirs(self.docs_dir, exist_ok=True)
        os.makedirs(os.path.join(self.docs_dir, "pdfs"), exist_ok=True)

    async def parse_document(self, pdf_path: str) -> dict:
        """
        Parses a project document (Contractor letter, Client request, etc.) using PyMuPDF 
        for local text extraction and Gemini for structured analytical claims analysis.
        """
        logger.info(f"Starting parsing of document: {pdf_path}")
        
        # 1. Local text extraction using PyMuPDF (fitz)
        extracted_text = ""
        is_scanned = False
        try:
            doc = fitz.open(pdf_path)
            for i in range(len(doc)):
                page = doc[i]
                extracted_text += f"\n--- Page {i+1} ---\n"
                page_text = page.get_text()
                extracted_text += page_text
            
            # If total extracted text is very short, treat as scanned and use high-resolution vision OCR fallback
            if len(extracted_text.strip()) < 150:
                is_scanned = True
                logger.info("PDF has very low text content. Activating high-resolution page rendering fallback.")
                
            doc.close()
        except Exception as e:
            logger.error(f"PyMuPDF text extraction failed: {e}")
            extracted_text = "Failed to extract text locally."
            is_scanned = True

        # 2. Formulate a rich claim and analysis prompt for Gemini
        prompt = """
        You are an expert Construction Claim Analyst, Project Management Consultant, and Legal Compliance Review AI for high-value housing projects.
        
        Analyze the attached project document (which could be a letter, formal request, EOT claim, site instruction, warning, or general report/minutes/lab tests) 
        for the Makindu Affordable Housing Project.
        
        CRITICAL ENGINEERING STANDARDS FOR LAB CUBE TESTS:
        If the document contains concrete compressive cube crushing test results (BS 1881 / KS EAS 18-1 codes), you MUST check the age of the concrete at crushing:
        1. 7-Day / 8-Day Early Tests: Do NOT evaluate these early indicators against the final 28-day design strength class. Instead, apply the standard civil engineering rule where 7-day strength should yield approximately 65% to 70% of the 28-day characteristic strength:
           - Class C25/20 (M25): Expected strength at 7 days is >= 17 N/mm2.
           - Class C30/25 (M30): Expected strength at 7 days is >= 20 N/mm2.
           - Class C15/12 (M15): Expected strength at 7 days is >= 10 N/mm2.
        2. Strict Alarm Thresholds:
           - If a 7-day or 8-day result meets or exceeds this 65% limit (e.g. achieving 18 N/mm2 on a C25 mix), classify the sample as "Passing / On Track" and state that there are no immediate contractual risks or liquidated damages exposures related to concrete quality.
           - Only flag a concrete strength failure as a critical risk if a 28-day test falls below the designated target, or if a 7-day test is significantly deficient (below the 60% mark).
        
        Extract the following structured fields in valid JSON matching this schema:
        {
            "title": "string (the official subject, title, or a concise logical identifier for this document)",
            "summary": "string (a concise, 2-3 sentence executive summary of the document's main points)",
            "detailed_analysis": "string (a highly detailed breakdown of what is discussed, including concrete strength analysis with specific crushing ages, concrete classes, and actual values if applicable)",
            "requests_made": ["string (a list of all specific requests made by the sender - e.g., extension of time, payments, material approvals, additional info)"],
            "action_items": ["string (a list of all concrete actions, decisions, or approvals required from the recipient)"],
            "contractual_implications": "string (any potential contractual risks, liquidated damages implications, timeline adjustments, or concrete quality risks evaluating early ages correctly)"
        }
        
        Return ONLY valid JSON.
        """

        try:
            logger.info("Attempting native multi-page multimodal PDF scan...")
            # Send the PDF directly to Gemini for complete analysis (Gemini 2.5 Flash handles scanned/multimodal PDFs natively!)
            result = await generate_structured_data(prompt, pdf_path, mime_type="application/pdf")
            if isinstance(result, dict):
                # Include local text if digital, otherwise note that visual OCR was applied
                result["verbatim_text"] = extracted_text if not is_scanned else "[Scanned Document / Native Multimodal PDF OCR Applied]"
                return result
        except Exception as native_err:
            logger.error(f"Native Gemini PDF analysis failed: {native_err}. Trying fallbacks...")
            
            # If native call fails, we try visual OCR if it's scanned
            if is_scanned:
                try:
                    logger.info("Running legacy visual OCR fallback (Page 1 rendering)...")
                    doc = fitz.open(pdf_path)
                    page = doc[0] # Focus on page 1 for quick metadata fallback
                    
                    # Check dimensions and scale up proportionately to capture small lettering beautifully!
                    rect = page.rect
                    scale = 3.0 # Default 3x zoom (approx 216 DPI)
                    if rect.width > 2000 or rect.height > 2000:
                        scale = 4.0 # For huge engineering A0/A1 sheets, scale 4x (approx 288 DPI) for hyper-clarity
                        
                    mat = fitz.Matrix(scale, scale)
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Save high-resolution preview slice
                    preview_path = pdf_path.replace(".pdf", "_hires_page.png")
                    pix.save(preview_path)
                    doc.close()
                    
                    # Send the high-res upscaled image to Gemini Vision
                    result = await generate_structured_data(prompt, preview_path, mime_type="image/png")
                    
                    # Cleanup preview
                    if os.path.exists(preview_path):
                        os.remove(preview_path)
                        
                    if isinstance(result, dict):
                        result["verbatim_text"] = "[Scanned Document / Visual OCR Fallback Applied]"
                        return result
                except Exception as visual_err:
                    logger.error(f"Visual OCR fallback failed: {visual_err}")
            
            # If visual OCR fallback fails OR it was not scanned to begin with, fall back to text-only analysis
            logger.info("Running text-only fallback analysis...")
            fallback_prompt = f"""
            Analyze the following text content of a construction project document and extract details in valid JSON matching this schema:
            {{
                "title": "string",
                "summary": "string",
                "detailed_analysis": "string",
                "requests_made": ["string"],
                "action_items": ["string"],
                "contractual_implications": "string"
            }}
            
            TEXT:
            {extracted_text[:15000]} # Cap text to prevent huge prompts
            """
            from ai_client import generate_summary_json
            try:
                result = await generate_summary_json(fallback_prompt)
                if isinstance(result, dict):
                    result["verbatim_text"] = extracted_text
                    return result
            except Exception as fallback_err:
                logger.error(f"Fallback text analysis failed: {fallback_err}")
        
        # Safe baseline fallback
        filename = os.path.basename(pdf_path)
        return {
            "title": filename.replace(".pdf", "").replace("_", " ").title(),
            "summary": "Uploaded project document.",
            "detailed_analysis": "Unable to perform advanced AI analysis due to system error.",
            "requests_made": [],
            "action_items": [],
            "contractual_implications": "Unknown",
            "verbatim_text": extracted_text
        }
