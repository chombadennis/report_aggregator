# Makindu AHP Field Intelligence & Reporting

A full-stack web application for automating construction site report compilation and analytics. It processes daily PDF site reports using AI-powered vision parsing to generate consolidated weekly and monthly Word documents, ready for distribution.

## Features

- **Daily → Weekly Aggregation**: Upload 7 daily PDF reports to generate a consolidated weekly Word document.
- **Weekly → Monthly Aggregation**: Upload 4 weekly PDF reports to generate a monthly Word document.
- **AI-Powered Vision Parsing**: Uses Google Vertex AI (Gemini 2.5 Flash/Pro) to extract structured data from PDF screenshots — capturing labour, weather, materials, machinery, instructions, and more.
- **Advanced Project Analytics & Trends**: Provides comprehensive historical tracking, AI analysis for performance trends, and deterministic, non-alarmist risk verdicts.
- **Financial & Production Calculations**: Automates complex contract summaries, financial tracking, and precise production metrics against stable, non-rolling monthly baseline targets.
- **Dual-Project Round-Robin Load Balancing**: Distributes Vertex AI requests across two Google Cloud projects to maximise quota and avoid rate limits (429 → 90s cool-down, 500/503 → exponential backoff).
- **SHA256 Fingerprint Caching**: Identical PDFs are never AI-scanned twice. Per-file and per-page caches allow full pipeline resumption after interruptions.
- **Strict Section Separation**: Prompt engineering enforces a hard boundary between Section F (daily works carried out) and Section Q (cumulative summary of works to date) to prevent data bleed.
- **Template-Based Word Generation**: Injects AI-extracted data into pre-designed `.docx` templates (`weekly_template.docx`, `monthly_template.docx`) while preserving logos, photos, and formatting.
- **Duplicate Report Guard**: API endpoint checks history before accepting a new report title.
- **Next.js Frontend**: Clean web interface for file uploads, metadata entry, and report download.

## Architecture

```
report_aggregator/
├── backend/          # FastAPI (Python) server
│   ├── main.py       # API entry point & request orchestration
│   ├── ai_client.py  # Vertex AI client (dual-project load balancer, token cache)
│   ├── parser.py     # PDF → screenshots → AI vision extraction (with caching)
│   ├── aggregator.py # Merges daily/weekly results into summary data
│   ├── generator.py  # Injects data into Word .docx templates
│   ├── monthly_aggregator.py # Merges weekly results into monthly summary data
│   ├── monthly_generator.py  # Injects monthly data into Word .docx templates
│   ├── financial_engine.py   # Calculates contract sums, baseline targets, & production metrics
│   ├── analytics.py          # Performs trend analysis, historical tracking, and deterministic risk verdicts
│   ├── contract_parser.py    # Extracts structured contract summaries
│   ├── audit_generator.py    # Ensures report documentation reflects accurate financial & production metrics
│   └── schemas.py    # Pydantic data models (DailyReportSchema, etc.)
└── frontend/         # Next.js (React/TypeScript) web application
```

### Backend Module Details

| Module | Responsibility |
|---|---|
| `main.py` | FastAPI app. Receives uploads, runs parse → aggregate → generate pipeline, returns the `.docx` file. |
| `ai_client.py` | Manages two GCP service account credentials in a round-robin pool. Fetches and caches OAuth2 tokens. Calls Vertex AI for both vision (PDF pages) and text-only (summary generation) tasks. |
| `parser.py` | Converts each PDF page to a high-res screenshot, then calls the AI vision endpoint. Uses SHA256 fingerprinting for per-file and per-page result caching. Intelligently skips non-data pages (Scope of Works, Progress Photos). |
| `aggregator.py` | Compiles 7 daily reports into a weekly summary: adaptive labour matrix, weather grid, material totals, machinery status, AI-generated professional works summary (via `generate_summary_json`), deduplication of challenges and instructions. |
| `generator.py` | Loads the `.docx` template, locates tables by their header text, and injects the aggregated data. Handles labour, weather, works, materials, machinery, instructions, interns, and text sections (Security, H&S, Visitors, Challenges). |
| `monthly_aggregator.py` | Compiles 4 weekly reports into a consolidated monthly summary. |
| `monthly_generator.py` | Injects the aggregated monthly data into the `monthly_template.docx`. |
| `financial_engine.py` | Calculates and tracks project costs against stable, non-rolling monthly baseline targets, ensuring consistent financial reporting. |
| `analytics.py` | Tracks historical progress and performance metrics to generate deterministic, non-alarmist risk verdicts and trend analysis. |
| `contract_parser.py` | Extracts and structures essential contract details and statuses for reporting integration. |
| `audit_generator.py` | Synchronises generated report documentation with accurate analytical and financial metrics. |
| `schemas.py` | Pydantic models defining the JSON contract between the AI parser and the rest of the pipeline. |

## Setup

### Prerequisites
- Python 3.11 (CRITICAL: 3.12, 3.13, and 3.14 are not supported due to dependency constraints)
- Node.js 18+
- Two Google Cloud service account JSON keys with Vertex AI access (one minimum, two recommended for load balancing).
- Word document templates: `weekly_template.docx` and `monthly_template.docx` in the `backend/` folder.

### Backend
```bash
cd backend
pip install -r requirements.txt
# Create a .env file with your credentials (see .env.example)
python main.py
# Server starts on http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# App runs on http://localhost:3000
```

## Environment Variables (`.env`)

| Variable | Description |
|---|---|
| `GOOGLE_CREDENTIALS_JSON` | JSON string of GCP Service Account #1 |
| `GOOGLE_CREDENTIALS_JSON_2` | JSON string of GCP Service Account #2 (optional, enables load balancing) |
| `GOOGLE_CLOUD_LOCATION` | Vertex AI region (default: `us-central1`) |

## Usage
1. Start both the backend (`python main.py`) and frontend (`npm run dev`) servers.
2. Open `http://localhost:3000` in your browser.
3. Upload the required PDF reports and fill in the report metadata (title, dates, % completion).
4. Click **Generate** and download the produced Word document.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/check-duplicate?title=<title>` | Returns `{"exists": true/false}` for duplicate title detection. |
| `POST` | `/api/generate-weekly` | Accepts 7 daily PDFs + form metadata. Returns a `.docx` weekly report. |
| `POST` | `/api/generate-monthly` | Accepts 4 weekly PDFs + form metadata. Returns a `.docx` monthly report. |

## Dependencies

- **Backend**: `fastapi`, `uvicorn`, `python-docx`, `PyMuPDF (fitz)`, `httpx`, `google-auth`, `pydantic`, `python-dotenv`
- **Frontend**: Next.js, React, TypeScript, Tailwind CSS, Lucide Icons
