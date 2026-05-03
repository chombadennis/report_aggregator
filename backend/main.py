from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.background import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
import asyncio
from typing import List
from parser import ReportParser
from aggregator import Aggregator
from generator import ReportGenerator
from monthly_aggregator import MonthlyAggregator
from monthly_generator import MonthlyReportGenerator

app = FastAPI(title="Construction Report Aggregator")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

parser = ReportParser()
aggregator = Aggregator()
monthly_parser = ReportParser(cache_dir="cache_monthly")
monthly_aggregator = MonthlyAggregator(history_dir="history_monthly")

@app.get("/api/check-duplicate")
async def check_duplicate(title: str):
    exists = aggregator.check_duplicate(title)
    return {"exists": exists}

@app.post("/api/generate-weekly")
async def generate_weekly(
    files: List[UploadFile] = File(...),
    title: str = Form(""),
    report_date: str = Form(""), # This handles the 'Dates' field (6th-12th April)
    time_elapsed: str = Form(""),
    pct_period: str = Form(""),
    pct_work: str = Form("")
):
    if len(files) != 7:
        raise HTTPException(status_code=400, detail=f"Validation Error: Exactly 7 daily reports are required. You uploaded {len(files)}.")
    
    non_pdfs = [f.filename for f in files if not f.filename.lower().endswith('.pdf')]
    if non_pdfs:
        raise HTTPException(status_code=400, detail=f"Validation Error: All uploads must be PDF files. Non-PDF detected: {', '.join(non_pdfs)}")
    
    if not report_date.strip():
        raise HTTPException(status_code=400, detail="Validation Error: 'Reporting Period' is required.")

    session_id = str(uuid.uuid4())
    session_dir = os.path.join(TEMP_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    try:
        # 1. Save and Verify Uploads
        pdf_paths = []
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail=f"File Error: '{file.filename}' is not a PDF.")
            
            path = os.path.join(session_dir, file.filename)
            with open(path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            pdf_paths.append(path)

        # 2. AI Parsing Phase (Parallel)
        tasks = [parser.parse_report(path, session_dir, "DAILY") for path in pdf_paths]
        try:
            daily_results = await asyncio.gather(*tasks)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI Scan Error: One or more reports failed to process. {str(e)}")

        # 3. Aggregation Phase (await the async call)
        try:
            weekly_summary = await aggregator.compile_weekly_data(daily_results)
            weekly_summary.update({
                "title": title, "report_date": report_date,
                "time_elapsed": time_elapsed, "pct_period": pct_period, "pct_work": pct_work
            })
        except ValueError as ve:
            raise HTTPException(status_code=422, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Data Error: Failed to compile the 7-day summary. {str(e)}")

        # 4. Document Generation Phase
        template_path = "weekly_template.docx"
        if not os.path.exists(template_path):
             raise HTTPException(status_code=500, detail="System Error: 'weekly_template.docx' missing from backend folder.")

        output_path = os.path.join(session_dir, "Generated_Weekly_Report.docx")
        try:
            generator = ReportGenerator(template_path)
            generator.generate_report(output_path, weekly_summary, "WEEKLY")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Template Error: Failed to write to the Word document. {str(e)}")

        # 5. Return File and Cleanup
        bg = BackgroundTasks()
        bg.add_task(shutil.rmtree, session_dir, ignore_errors=True)
        return FileResponse(output_path, filename=f"Weekly_Report_{report_date.replace(' ', '_')}.docx", background=bg)

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")

@app.post("/api/generate-monthly")
async def generate_monthly(
    files: List[UploadFile] = File(...),
    title: str = Form(""),
    report_date: str = Form(""),
    time_elapsed: str = Form(""),
    pct_period: str = Form(""),
    pct_work: str = Form("")
):
    if not (4 <= len(files) <= 6):
        raise HTTPException(status_code=400, detail=f"Validation Error: Exactly 4 to 6 weekly reports are required. You uploaded {len(files)}.")

    non_pdfs = [f.filename for f in files if not f.filename.lower().endswith('.pdf')]
    if non_pdfs:
        raise HTTPException(status_code=400, detail=f"Validation Error: All uploads must be PDF files. Non-PDF detected: {', '.join(non_pdfs)}")

    session_id = str(uuid.uuid4())
    session_dir = os.path.join(TEMP_DIR, f"monthly_{session_id}")
    os.makedirs(session_dir, exist_ok=True)

    try:
        # 1. Save Uploads
        pdf_paths = []
        for file in files:
            path = os.path.join(session_dir, file.filename)
            with open(path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            pdf_paths.append(path)

        # 2. AI Parsing Phase (Parallel - Limited to 2 at a time)
        semaphore = asyncio.Semaphore(2)
        async def parse_task(p):
            async with semaphore:
                return await monthly_parser.parse_report(p, session_dir, "WEEKLY")
        
        tasks = [parse_task(path) for path in pdf_paths]
        try:
            weekly_results = await asyncio.gather(*tasks)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI Scan Error: One or more weekly reports failed to process. {str(e)}")

        # 3. Aggregation Phase
        try:
            metadata = {
                "title": title,
                "report_date": report_date,
                "time_elapsed": time_elapsed,
                "pct_period": pct_period,
                "pct_work": pct_work
            }
            monthly_summary = monthly_aggregator.compile_monthly_data(weekly_results, metadata)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Data Error: Failed to compile the monthly summary. {str(e)}")

        # 4. Document Generation Phase
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monthly_report_template.docx")
        if not os.path.exists(template_path):
             raise HTTPException(status_code=500, detail="System Error: 'monthly_report_template.docx' missing from backend folder.")

        output_path = os.path.join(session_dir, "Generated_Monthly_Report.docx")
        try:
            generator = MonthlyReportGenerator(template_path)
            generator.generate_report(output_path, monthly_summary)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Template Error: Failed to write to the Monthly Word document. {str(e)}")

        # 5. Return File and Cleanup
        bg = BackgroundTasks()
        bg.add_task(shutil.rmtree, session_dir, ignore_errors=True)
        filename_clean = title.replace(" ", "_").replace("(", "").replace(")", "")
        return FileResponse(output_path, filename=f"{filename_clean}.docx", background=bg)

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
