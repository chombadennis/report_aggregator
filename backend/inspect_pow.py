import fitz
import os

pdf_path = r"e:\MyProjects\maks_ahp\POW-Proposed Makindu AHP..pdf"

if not os.path.exists(pdf_path):
    print("PDF not found at", pdf_path)
    exit(1)

doc = fitz.open(pdf_path)
print(f"Number of pages: {len(doc)}")

for page_idx in range(len(doc)):
    page = doc[page_idx]
    rect = page.rect
    print(f"\n--- Page {page_idx + 1} Dimensions: width={rect.width}, height={rect.height} ---")
    
    # Try to extract text first
    text = page.get_text()
    print(f"Extracted Text Length: {len(text)} characters")
    if text:
        print("First 300 characters of text:")
        print(text[:300])
        print("...")
    else:
        print("No readable text found on this page (likely image-only or scanned).")

doc.close()
