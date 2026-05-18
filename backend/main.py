from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
import asyncio
import json
from typing import List
from datetime import datetime
from parser import ReportParser
from aggregator import Aggregator
from generator import ReportGenerator
from monthly_aggregator import MonthlyAggregator
from monthly_generator import MonthlyReportGenerator
from contract_parser import ContractParser
from analytics import AnalyticsEngine
from audit_generator import AuditReportGenerator
from financial_engine import FinancialEngine
from document_parser import DocumentParser

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

parser = ReportParser(cache_dir="cache")
aggregator = Aggregator()
monthly_parser = ReportParser(cache_dir="cache")
monthly_aggregator = MonthlyAggregator(history_dir="cache/history_monthly")
contract_parser = ContractParser(cache_dir="cache")
analytics_engine = AnalyticsEngine(history_dir="history", monthly_dir="cache/history_monthly")
audit_generator = AuditReportGenerator()
financial_engine = FinancialEngine()
document_parser = DocumentParser(cache_dir="cache")

@app.get("/api/check-duplicate")
async def check_duplicate(title: str):
    exists = aggregator.check_duplicate(title)
    return {"exists": exists}

@app.post("/api/generate-weekly-stream")
async def generate_weekly_stream(
    files: List[UploadFile] = File(...),
    title: str = Form(""),
    report_date: str = Form(""),
    time_elapsed: str = Form(""),
    pct_period: str = Form(""),
    pct_work: str = Form("")
):
    """Weekly generation with Server-Sent Events for real-time progress."""
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(TEMP_DIR, f"weekly_stream_{session_id}")
    os.makedirs(session_dir, exist_ok=True)

    async def event_generator():
        try:
            yield f"data: {json.dumps({'status': 'uploading', 'msg': '📦 Uploading daily logs...'})}\n\n"
            
            pdf_paths = []
            for file in files:
                path = os.path.join(session_dir, file.filename)
                with open(path, "wb") as f:
                    shutil.copyfileobj(file.file, f)
                pdf_paths.append(path)

            yield f"data: {json.dumps({'status': 'scanning', 'msg': '📡 Initializing AI Vision Scan...'})}\n\n"

            results = [None] * len(pdf_paths)
            for idx, path in enumerate(pdf_paths):
                filename = os.path.basename(path)
                yield f"data: {json.dumps({'status': 'scanning', 'msg': f'🔍 [Phase {idx+1}/{len(pdf_paths)}] Processing {filename}...'})}\n\n"
                res = await parser.parse_report(path, session_dir, "DAILY")
                results[idx] = res

            yield f"data: {json.dumps({'status': 'aggregating', 'msg': '📊 Compiling 7-day summary...'})}\n\n"
            
            weekly_summary = await aggregator.compile_weekly_data(results)
            weekly_summary.update({
                "title": title, "report_date": report_date,
                "time_elapsed": time_elapsed, "pct_period": pct_period, "pct_work": pct_work
            })
            aggregator._save_to_history(weekly_summary, "WEEKLY")

            yield f"data: {json.dumps({'status': 'generating', 'msg': '📝 Finalizing Word Document...'})}\n\n"
            
            template_path = "weekly_template.docx"
            output_docx = os.path.join(session_dir, "Weekly_Report.docx")
            
            generator = ReportGenerator(template_path)
            generator.generate_report(output_docx, weekly_summary, "WEEKLY")

            yield f"data: {json.dumps({'status': 'done', 'session_id': session_id, 'msg': '✨ Weekly Report Ready!'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'msg': f'❌ Error: {str(e)}'})}\n\n"
        
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/generate-monthly-stream")
async def generate_monthly_stream(
    files: List[UploadFile] = File(...),
    title: str = Form(""),
    report_date: str = Form(""),
    time_elapsed: str = Form(""),
    pct_period: str = Form(""),
    pct_work: str = Form("")
):
    """Monthly generation with Server-Sent Events for real-time progress."""
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(TEMP_DIR, f"monthly_stream_{session_id}")
    os.makedirs(session_dir, exist_ok=True)

    async def event_generator():
        try:
            yield f"data: {json.dumps({'status': 'uploading', 'msg': '📦 Uploading reports to server...'})}\n\n"
            
            pdf_paths = []
            for file in files:
                path = os.path.join(session_dir, file.filename)
                with open(path, "wb") as f:
                    shutil.copyfileobj(file.file, f)
                pdf_paths.append(path)

            yield f"data: {json.dumps({'status': 'scanning', 'msg': '📡 Initializing AI Vision Scan...'})}\n\n"

            results = [None] * len(pdf_paths)
            for idx, path in enumerate(pdf_paths):
                filename = os.path.basename(path)
                yield f"data: {json.dumps({'status': 'scanning', 'msg': f'🔍 [Phase {idx+1}/{len(pdf_paths)}] Processing {filename}...'})}\n\n"
                res = await monthly_parser.parse_report(path, session_dir, "WEEKLY")
                results[idx] = res

            metadata = {
                "title": title, "report_date": report_date,
                "time_elapsed": time_elapsed, "pct_period": pct_period, "pct_work": pct_work
            }
            
            # --- CHRONOLOGY VALIDATION ---
            month_num, target_year = monthly_aggregator._parse_month_year(title)
            if month_num:
                yield f"data: {json.dumps({'status': 'validating', 'msg': '🧐 Verifying chronology and month alignment...'})}\n\n"
                val_warnings = monthly_aggregator.validate_chronology(results, month_num, target_year)
                for warn in val_warnings:
                    yield f"data: {json.dumps({'status': 'warning', 'msg': warn})}\n\n"
                    # Small delay so user can see multiple warnings
                    await asyncio.sleep(0.5)

            monthly_summary = monthly_aggregator.compile_monthly_data(results, metadata)

            yield f"data: {json.dumps({'status': 'generating', 'msg': '📝 Finalizing Word Document...'})}\n\n"
            
            template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monthly_report_template.docx")
            output_docx = os.path.join(session_dir, "Monthly_Report.docx")
            
            generator = MonthlyReportGenerator(template_path)
            generator.generate_report(output_docx, monthly_summary)

            yield f"data: {json.dumps({'status': 'done', 'session_id': session_id, 'msg': '✨ Report Ready for Download!'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'msg': f'❌ Error: {str(e)}'})}\n\n"
        
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/download-session/{session_id}")
async def download_session(session_id: str, background_tasks: BackgroundTasks):
    # Find the directory
    possible_dirs = [d for d in os.listdir(TEMP_DIR) if session_id in d]
    if not possible_dirs:
        raise HTTPException(status_code=404, detail="File expired or not found.")
    
    target_dir = os.path.join(TEMP_DIR, possible_dirs[0])
    # Handle both weekly and monthly filenames
    file_path = os.path.join(target_dir, "Monthly_Report.docx")
    if not os.path.exists(file_path):
        file_path = os.path.join(target_dir, "Weekly_Report.docx")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document failed to generate.")
    
    background_tasks.add_task(shutil.rmtree, target_dir, ignore_errors=True)
    prefix = "Monthly" if "monthly" in target_dir else "Weekly"
    return FileResponse(file_path, filename=f"{prefix}_Report_{session_id[:8]}.docx")

@app.get("/api/contract-summary")
async def get_contract_summary():
    data = contract_parser.get_contract_summary()
    if not data:
        return {"msg": "No contract summary found. Please upload a report to extract details."}
    return data


@app.get("/api/trends")
async def get_trends():
    """
    Analyzes historical JSONs chronologically to provide trend data.
    """
    return analytics_engine.get_historical_trends()

@app.get("/api/ai-insights")
async def get_ai_insights():
    """
    Feeds the historical trend data to Gemini for a management-level executive summary.
    """
    trends = analytics_engine.get_historical_trends()
    contract = contract_parser.get_contract_summary()
    return await analytics_engine.generate_ai_insights(trends, contract)

@app.get("/api/analytics/trends")
async def get_trends():
    """Returns the comprehensive historical trend data."""
    trends = analytics_engine.get_historical_trends()
    daily = analytics_engine.get_daily_trends()
    return {
        "weekly": trends,
        "daily": daily
    }

@app.get("/api/analytics/financials")
async def get_financials():
    """Serves the materialized financial analysis data. Always computes to ensure real-time accuracy."""
    return financial_engine.compute_and_cache_financials()

@app.get("/api/analytics/correlations")
async def get_correlations():
    """Returns data for scatter plots and heatmaps."""
    financials = financial_engine.compute_and_cache_financials()
    return analytics_engine.get_correlations(financials)

@app.get("/api/analytics/insights")
async def get_insights():
    """Triggers AI analysis of current trends."""
    trends = analytics_engine.get_historical_trends()
    financials = financial_engine.compute_and_cache_financials()
    
    context = {}
    context_path = "cache/contract_summary.json"
    if os.path.exists(context_path):
        with open(context_path, "r") as f:
            context = json.load(f)
    
    insights = await analytics_engine.generate_ai_insights(trends, context, financials)
    return insights

@app.get("/api/generate-audit-report")
async def generate_audit_report(background_tasks: BackgroundTasks):
    """Generates a full audit report document based on current trends and AI insights."""
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(TEMP_DIR, f"audit_{session_id}")
    os.makedirs(session_dir, exist_ok=True)
    
    try:
        # 1. Gather data
        trends = analytics_engine.get_historical_trends()
        financials = financial_engine.compute_and_cache_financials()
        
        context = {}
        context_path = "cache/contract_summary.json"
        if os.path.exists(context_path):
            with open(context_path, "r") as f:
                context = json.load(f)
        
        # 2. Get AI Insights
        insights = await analytics_engine.generate_ai_insights(trends, context, financials)
        
        # 3. Generate Document
        output_docx = os.path.join(session_dir, "Audit_Report.docx")
        audit_generator.generate_report(output_docx, trends, insights, financials)
        
        # 4. Return file (don't delete immediately, let download-session handle it if we want, 
        # or just return it now and delete later)
        return FileResponse(
            output_docx, 
            filename=f"Audit_Report_{datetime.now().strftime('%Y%m%d')}.docx",
            background=background_tasks.add_task(shutil.rmtree, session_dir, ignore_errors=True)
        )
    except Exception as e:
        shutil.rmtree(session_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(""),
    summary: str = Form(""),
    date_sent: str = Form(""),
    category: str = Form(""),
    sender: str = Form(""),
    recipient: str = Form("")
):
    try:
        doc_id = str(uuid.uuid4())
        docs_dir = os.path.join("cache", "project_documents")
        pdfs_dir = os.path.join(docs_dir, "pdfs")
        os.makedirs(pdfs_dir, exist_ok=True)
        
        pdf_filename = f"{doc_id}.pdf"
        pdf_path = os.path.join(pdfs_dir, pdf_filename)
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
            
        parsed_data = await document_parser.parse_document(pdf_path)
        
        final_title = title.strip() if title.strip() else parsed_data.get("title", file.filename)
        final_summary = summary.strip() if summary.strip() else parsed_data.get("summary", "")
        
        final_sender = sender.strip()
        final_recipient = recipient.strip()
        if category == "contractor":
            final_sender = "Contractor"
        elif category == "client":
            final_sender = "Client / Project Manager"
            
        final_date_sent = date_sent.strip() if date_sent.strip() else datetime.now().strftime("%Y-%m-%d")
        
        doc_metadata = {
            "id": doc_id,
            "title": final_title,
            "summary": final_summary,
            "date_uploaded": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date_sent": final_date_sent,
            "category": category,
            "sender": final_sender,
            "recipient": final_recipient,
            "pdf_path": pdf_path,
            "ai_analysis": {
                "title": parsed_data.get("title"),
                "summary": parsed_data.get("summary"),
                "detailed_analysis": parsed_data.get("detailed_analysis"),
                "requests_made": parsed_data.get("requests_made", []),
                "action_items": parsed_data.get("action_items", []),
                "contractual_implications": parsed_data.get("contractual_implications")
            },
            "verbatim_text": parsed_data.get("verbatim_text", "")
        }
        
        metadata_path = os.path.join(docs_dir, f"{doc_id}.json")
        with open(metadata_path, "w") as f:
            json.dump(doc_metadata, f, indent=2)
            
        return doc_metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@app.get("/api/project-documents")
async def get_project_documents():
    try:
        docs_dir = os.path.join("cache", "project_documents")
        if not os.path.exists(docs_dir):
            return []
            
        documents = []
        for f_name in os.listdir(docs_dir):
            if f_name.endswith(".json"):
                try:
                    with open(os.path.join(docs_dir, f_name), "r") as f:
                        doc_data = json.load(f)
                        doc_list_item = doc_data.copy()
                        if "verbatim_text" in doc_list_item:
                            del doc_list_item["verbatim_text"]
                        documents.append(doc_list_item)
                except:
                    continue
                    
        documents.sort(key=lambda x: x.get("date_sent", ""), reverse=True)
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/project-documents/{doc_id}")
async def delete_project_document(doc_id: str):
    try:
        docs_dir = os.path.join("cache", "project_documents")
        metadata_path = os.path.join(docs_dir, f"{doc_id}.json")
        pdf_path = os.path.join(docs_dir, "pdfs", f"{doc_id}.pdf")
        
        deleted = False
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
            deleted = True
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            deleted = True
            
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found.")
            
        return {"status": "success", "msg": f"Document {doc_id} successfully deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
