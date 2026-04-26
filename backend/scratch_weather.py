import fitz
import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from ai_client import generate_structured_data

async def main():
    pdf_path = r"d:\maks_ahp\MAKINDU AHP DAILY PROGRESS REPORT Saturday 18th April 2026.pdf"
    doc = fitz.open(pdf_path)
    for i in range(len(doc)):
        text = doc[i].get_text().upper()
        if "WEATHER" in text and "SITE REPORT" in text:
            print(f"Found on page {i+1}")
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
            pix.save("temp_weather.png")
            prompt = "Look at the Weather subsection under E. SITE REPORT. Describe exactly how this table is structured (headers, rows, columns). What text, marks, or ticks are in it? Provide your description as a simple JSON string with the key 'description'."
            res = await generate_structured_data(prompt, "temp_weather.png", "image/png")
            print(res)
            break

asyncio.run(main())
