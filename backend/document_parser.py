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
        You are an expert Construction Claim Analyst, Project Management Consultant, and Legal Audit AI for high-value housing projects.
        
        Analyze the attached project document (which could be a letter, formal request, EOT claim, site instruction, warning, or general report/minutes) 
        for the Makindu Affordable Housing Project.
        
        Extract the following structured fields in valid JSON matching this schema:
        {
            "title": "string (the official subject, title, or a concise logical identifier for this document)",
            "summary": "string (a concise, 2-3 sentence executive summary of the document's main points)",
            "detailed_analysis": "string (a highly detailed breakdown of what is discussed, including issues, complaints, and timeline implications)",
            "requests_made": ["string (a list of all specific requests made by the sender - e.g., extension of time, payments, material approvals, additional info)"],
            "action_items": ["string (a list of all concrete actions, decisions, or approvals required from the recipient)"],
            "contractual_implications": "string (any potential contractual risks, liquidated damages implications, timeline adjustments, or cost claims)"
        }
        
        Return ONLY valid JSON.
        """

        try:
            if is_scanned:
                # Scanned fallback: Render high-resolution PNG page slices (zoomed in by 3x/300 DPI) for visual OCR
                doc = fitz.open(pdf_path)
                page = doc[0] # Focus on page 1 for quick metadata
                
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
            else:
                # Send the PDF directly to Gemini for complete analysis (Gemini 2.5 Flash handles PDFs natively!)
                result = await generate_structured_data(prompt, pdf_path, mime_type="application/pdf")
                if isinstance(result, dict):
                    # Include the local verbatim text extraction in the output
                    result["verbatim_text"] = extracted_text
                    return result
        except Exception as e:
            logger.error(f"Gemini document analysis failed: {e}. Falling back to text-only analysis.")
            # Text-only fallback
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
            except Exception as fe:
                logger.error(f"Fallback text analysis failed: {fe}")
        
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
