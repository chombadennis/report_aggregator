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

        # 2. AI Parsing Phase
        daily_results = []
        for i, path in enumerate(pdf_paths):
            try:
                data = await parser.parse_report(path, session_dir, "DAILY")
                daily_results.append(data)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"AI Scan Error: Failed to process report {i+1} ({os.path.basename(path)}). {str(e)}")

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
    if len(files) != 4:
        raise HTTPException(status_code=400, detail=f"Validation Error: Exactly 4 weekly reports are required. You uploaded {len(files)}.")

    non_pdfs = [f.filename for f in files if not f.filename.lower().endswith('.pdf')]
    if non_pdfs:
        raise HTTPException(status_code=400, detail=f"Validation Error: All uploads must be PDF files. Non-PDF detected: {', '.join(non_pdfs)}")

    session_id = str(uuid.uuid4())
    session_dir = os.path.join(TEMP_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    try:
        # 1. Save Uploads
        pdf_paths = []
        for file in files:
            path = os.path.join(session_dir, file.filename)
            with open(path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            pdf_paths.append(path)

        # 2. AI Parsing Phase
        weekly_results = []
        for i, path in enumerate(pdf_paths):
            try:
                data = await parser.parse_report(path, session_dir, "DAILY")
                weekly_results.append(data)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"AI Scan Error: Failed to process Weekly report {i+1} ({os.path.basename(path)}). {str(e)}")

        # 3. Aggregation Phase
        try:
            # compile_monthly_data is currently sync, but we should verify if it should be async.
            # Looking at aggregator.py, it is sync. So no await needed here.
            monthly_summary = aggregator.compile_monthly_data(weekly_results)
            monthly_summary.update({
                "title": title, "report_date": report_date,
                "time_elapsed": time_elapsed, "pct_period": pct_period, "pct_work": pct_work
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Data Error: Failed to compile the monthly summary. {str(e)}")

        # 4. Document Generation Phase
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monthly_template.docx")
        if not os.path.exists(template_path):
             raise HTTPException(status_code=500, detail="System Error: 'monthly_template.docx' missing from backend folder.")

        output_path = os.path.join(session_dir, "Generated_Monthly_Report.docx")
        try:
            generator = ReportGenerator(template_path)
            generator.generate_report(output_path, monthly_summary, "MONTHLY")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Template Error: Failed to write to the Monthly Word document. {str(e)}")

        # 5. Return File and Cleanup
        bg = BackgroundTasks()
        bg.add_task(shutil.rmtree, session_dir, ignore_errors=True)
        return FileResponse(output_path, filename=f"Monthly_Report_{report_date.replace(' ', '_')}.docx", background=bg)

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
