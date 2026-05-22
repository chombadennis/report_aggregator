from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends, Header, status
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
from progress_generator import ProgressReportGenerator
from financial_engine import FinancialEngine
from document_parser import DocumentParser
from auth import clerk_verifier

app = FastAPI(title="Construction Report Aggregator")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp_uploads"
INSIGHTS_CACHE_PATH = os.path.join("cache", "ai_insights.json")
os.makedirs(TEMP_DIR, exist_ok=True)

parser = ReportParser(cache_dir="cache")
aggregator = Aggregator(history_dir="cache/history")
monthly_parser = ReportParser(cache_dir="cache")
monthly_aggregator = MonthlyAggregator(history_dir="cache/history_monthly")
contract_parser = ContractParser(cache_dir="cache")
analytics_engine = AnalyticsEngine(history_dir="cache/history", monthly_dir="cache/history_monthly")
progress_generator = ProgressReportGenerator()
financial_engine = FinancialEngine()
document_parser = DocumentParser(cache_dir="cache")

# --- AUTHENTICATION DEPENDENCIES ---
async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token. Please log in."
        )
    token = authorization.split(" ")[1]
    payload = clerk_verifier.verify_token(token)
    
    # Debug print to inspect Clerk JWT claims
    print(f"--- DEBUG AUTH: Decoded Clerk JWT payload keys: {list(payload.keys())} ---")
    print(f"--- DEBUG AUTH: Decoded Clerk JWT payload claims: {payload} ---")
    
    email = payload.get("email") or payload.get("email_address")
    if not email and "emails" in payload:
        emails = payload.get("emails")
        if isinstance(emails, list) and len(emails) > 0:
            email = emails[0]
            
    # Fallback: Query Clerk Backend API if email not in token claims
    user_id = payload.get("sub")
    if not email and user_id:
        clerk_secret_key = os.getenv("CLERK_SECRET_KEY")
        if clerk_secret_key:
            try:
                import httpx
                headers = {"Authorization": f"Bearer {clerk_secret_key}"}
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"https://api.clerk.com/v1/users/{user_id}", headers=headers)
                    if response.status_code == 200:
                        user_data = response.json()
                        email_addresses = user_data.get("email_addresses", [])
                        primary_email_id = user_data.get("primary_email_address_id")
                        
                        # Match primary email ID
                        for e_addr in email_addresses:
                            if e_addr.get("id") == primary_email_id:
                                email = e_addr.get("email_address")
                                break
                        
                        # Fallback to the first email if primary not matched
                        if not email and email_addresses:
                            email = email_addresses[0].get("email_address")
                            
                        print(f"--- DEBUG AUTH: Resolved email '{email}' from Clerk API for user '{user_id}' ---")
                    else:
                        print(f"--- DEBUG AUTH: Failed to fetch user from Clerk API. Status: {response.status_code}, Body: {response.text} ---")
            except Exception as ex:
                print(f"--- DEBUG AUTH: Exception when fetching user from Clerk API: {ex} ---")
            
    return {
        "email": email,
        "user_id": user_id,
        "claims": payload
    }

async def require_admin(current_user: dict = Depends(get_current_user)):
    admin_email = os.getenv("ADMIN_EMAIL")
    if not admin_email:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ADMIN_EMAIL configuration is missing in the backend server."
        )
    
    user_email = current_user.get("email")
    if not user_email or user_email.lower() != admin_email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: This account is restricted to read-only access. You do not have permission to execute write or AI generation commands."
        )
    return current_user

@app.get("/api/ping")
async def ping():
    """Lightweight public keep-alive endpoint for UptimeRobot pings."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/check-duplicate")
async def check_duplicate(title: str, current_user: dict = Depends(get_current_user)):
    exists = aggregator.check_duplicate(title)
    return {"exists": exists}

@app.post("/api/generate-weekly-stream")
async def generate_weekly_stream(
    files: List[UploadFile] = File(...),
    title: str = Form(""),
    report_date: str = Form(""),
    time_elapsed: str = Form(""),
    pct_period: str = Form(""),
    pct_work: str = Form(""),
    current_user: dict = Depends(require_admin)
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
    pct_work: str = Form(""),
    current_user: dict = Depends(require_admin)
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
async def get_contract_summary(current_user: dict = Depends(get_current_user)):
    data = contract_parser.get_contract_summary()
    if not data:
        return {"msg": "No contract summary found. Please upload a report to extract details."}
    return data


@app.get("/api/trends")
async def get_trends(current_user: dict = Depends(get_current_user)):
    """
    Analyzes historical JSONs chronologically to provide trend data.
    """
    return analytics_engine.get_historical_trends()

@app.get("/api/ai-insights")
async def get_ai_insights(current_user: dict = Depends(get_current_user)):
    """
    Feeds the historical trend data to Gemini for a management-level executive summary.
    """
    trends = analytics_engine.get_historical_trends()
    contract = contract_parser.get_contract_summary()
    return await analytics_engine.generate_ai_insights(trends, contract)

@app.get("/api/analytics/trends")
async def get_trends(current_user: dict = Depends(get_current_user)):
    """Returns the comprehensive historical trend data."""
    trends = analytics_engine.get_historical_trends()
    daily = analytics_engine.get_daily_trends()
    return {
        "weekly": trends,
        "daily": daily
    }

@app.get("/api/analytics/financials")
async def get_financials(current_user: dict = Depends(get_current_user)):
    """Serves the materialized financial analysis data. Always computes to ensure real-time accuracy."""
    return financial_engine.compute_and_cache_financials()

@app.get("/api/analytics/correlations")
async def get_correlations(current_user: dict = Depends(get_current_user)):
    """Returns data for scatter plots and heatmaps."""
    financials = financial_engine.compute_and_cache_financials()
    return analytics_engine.get_correlations(financials)

@app.get("/api/analytics/insights")
async def get_insights(current_user: dict = Depends(get_current_user)):
    """
    Returns AI insights from persistent cache, or generates them on-demand if the user is an admin.
    """
    if os.path.exists(INSIGHTS_CACHE_PATH):
        try:
            with open(INSIGHTS_CACHE_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            pass

    # Cache does not exist. Check if user is admin
    admin_email = os.getenv("ADMIN_EMAIL")
    is_admin = False
    if current_user and admin_email:
        user_email = current_user.get("email")
        if user_email and user_email.lower() == admin_email.lower():
            is_admin = True

    if is_admin:
        trends = analytics_engine.get_historical_trends()
        financials = financial_engine.compute_and_cache_financials()
        
        context = {}
        context_path = "cache/contract_summary.json"
        if os.path.exists(context_path):
            with open(context_path, "r") as f:
                context = json.load(f)
        
        insights = await analytics_engine.generate_ai_insights(trends, context, financials)
        os.makedirs("cache", exist_ok=True)
        with open(INSIGHTS_CACHE_PATH, "w") as f:
            json.dump(insights, f, indent=2)
        return insights
    else:
        return {
            "swot": {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
            "recommendations": {"to_client": [], "to_contractor": []},
            "executive_summary": "Awaiting administrator to generate AI Insights.",
            "critical_advice": "",
            "claim_verdict": "Low",
            "is_empty": True
        }

@app.post("/api/analytics/insights/regenerate")
async def regenerate_insights(current_user: dict = Depends(require_admin)):
    """
    Forcefully regenerates and caches AI Insights from the current trends and documents.
    """
    trends = analytics_engine.get_historical_trends()
    financials = financial_engine.compute_and_cache_financials()
    
    context = {}
    context_path = "cache/contract_summary.json"
    if os.path.exists(context_path):
        with open(context_path, "r") as f:
            context = json.load(f)
            
    insights = await analytics_engine.generate_ai_insights(trends, context, financials)
    os.makedirs("cache", exist_ok=True)
    with open(INSIGHTS_CACHE_PATH, "w") as f:
        json.dump(insights, f, indent=2)
    return insights

@app.get("/api/generate-progress-report")
async def generate_progress_report(background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Generates a full progress report document based on current trends and AI insights."""
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(TEMP_DIR, f"progress_{session_id}")
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
        
        # 2. Retrieve AI Insights from persistent cache if available
        insights = None
        if os.path.exists(INSIGHTS_CACHE_PATH):
            try:
                with open(INSIGHTS_CACHE_PATH, "r") as f:
                    insights = json.load(f)
            except Exception:
                pass
                
        # If cache is not found, attempt on-demand generation ONLY if the user is an admin
        if not insights:
            admin_email = os.getenv("ADMIN_EMAIL")
            is_admin = False
            if current_user and admin_email:
                user_email = current_user.get("email")
                if user_email and user_email.lower() == admin_email.lower():
                    is_admin = True
                    
            if is_admin:
                insights = await analytics_engine.generate_ai_insights(trends, context, financials)
                os.makedirs("cache", exist_ok=True)
                with open(INSIGHTS_CACHE_PATH, "w") as f:
                    json.dump(insights, f, indent=2)
            else:
                insights = {
                    "swot": {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
                    "recommendations": {"to_client": [], "to_contractor": []},
                    "executive_summary": "Awaiting administrator to generate AI Insights.",
                    "critical_advice": "",
                    "claim_verdict": "Low",
                    "is_empty": True
                }
        
        # 3. Generate Document
        output_docx = os.path.join(session_dir, "Progress_Report.docx")
        progress_generator.generate_report(output_docx, trends, insights, financials)
        
        # 4. Return file (don't delete immediately, let download-session handle it if we want, 
        # or just return it now and delete later)
        return FileResponse(
            output_docx, 
            filename=f"Progress_Report_{datetime.now().strftime('%Y%m%d')}.docx",
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
    recipient: str = Form(""),
    current_user: dict = Depends(require_admin)
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
async def get_project_documents(current_user: dict = Depends(get_current_user)):
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
async def delete_project_document(doc_id: str, current_user: dict = Depends(require_admin)):
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

@app.post("/api/admin/restore-cache")
async def restore_cache(file: UploadFile = File(...), current_user: dict = Depends(require_admin)):
    """Allows the administrator to upload a ZIP archive of their local cache folder and extract it directly on the persistent disk."""
    import zipfile
    import io
    try:
        # Read the uploaded zip file bytes
        file_bytes = await file.read()
        
        # Open the zip archive in memory
        zip_archive = zipfile.ZipFile(io.BytesIO(file_bytes))
        
        # Verify it is a valid zip archive
        namelist = zip_archive.namelist()
        if not namelist:
            raise HTTPException(status_code=400, detail="The uploaded ZIP file is empty.")
            
        # Target extraction directory is the persistent "cache" directory
        target_dir = "cache"
        os.makedirs(target_dir, exist_ok=True)
        
        # Extract all files safely
        zip_archive.extractall(target_dir)
        
        return {
            "status": "success",
            "msg": f"Successfully restored cache! Extracted {len(namelist)} items directly onto the persistent disk."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract and restore cache: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
