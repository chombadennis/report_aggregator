# Project Site Analytics & Reporting

A comprehensive full-stack enterprise intelligence system for automating construction site report compilation, scheduling progress reviews, and performance analytics. It processes daily PDF site reports, letters, and Program of Works (PoW) plans using AI-powered vision parsing to generate consolidated weekly and monthly Word documents, perform dynamic financial calibrations, and compile executive contract compliance reviews.

## Features

- **Daily → Weekly Aggregation**: Upload 7 daily PDF reports to generate a consolidated weekly Word document with fully normalized layouts.
- **Weekly → Monthly Aggregation**: Upload 4 weekly PDF reports to generate a monthly Word document.
- **Program of Works (PoW) & Document Reviews**: Uploads and parses contractual project letters, schedules, and PoW plans to evaluate critical-path deadlines, contractual implications, risks, and extract actionable project manager tasks.
- **AI-Powered Vision Parsing**: Uses Google Vertex AI (Gemini 2.5 Flash/Pro) to extract structured data from PDF screenshots — capturing labour, weather, materials, machinery, instructions, and more.
- **Dynamic S-Curve & Financial Recalibrations**: Automates contract summaries, KES revenue accrual ledgers, and tracks progress against stable baseline and rolling dynamic monthly targets to calculate future weekly velocity rates.
- **Recalibration Executive Summaries**: Automatically analyzes completed month performance and ongoing month milestones, generating mathematical logic summaries of the cumulative Slippage Gap.
- **Interactive Trends Dashboard**: Interactive line charts of financial S-curves, schedule slippage gaps, and scrollable labor force momentum bars with interactive weather and material tooltips.
- **Real-Time Streaming Generation**: Implements Server-Sent Events (SSE) to stream generation phases in real-time, providing immediate visual feedback to frontend users.
- **Dual-Project Round-Robin Load Balancing**: Distributes Vertex AI requests across two Google Cloud projects to maximise quota and avoid rate limits (429 → 90s cool-down, 500/503 → exponential backoff).
- **SHA256 Fingerprint Caching**: Identical PDFs are never AI-scanned twice. Per-file and per-page caches allow full pipeline resumption after interruptions.
- **Strict Section Separation & Auto-Layout Normalization**: Prompt engineering prevents data bleed between sections, while a post-compilation routine dynamically aligns tables and paragraphs to preserve templates and prevent large indents.
- **Next.js Frontend**: Sleek dashboard for upload management, document reviews, trend analysis, and document downloads.


## Architecture

```
report_aggregator/
├── backend/          # FastAPI (Python) server
│   ├── main.py       # API entry point & request orchestration
│   ├── ai_client.py  # Vertex AI client (dual-project load balancer, token cache)
│   ├── parser.py     # PDF → screenshots → AI vision extraction (with caching)
│   ├── aggregator.py # Merges daily/weekly results into summary data
│   ├── generator.py  # Injects data into Word .docx templates & normalizes formatting
│   ├── monthly_aggregator.py # Merges weekly results into monthly summary data
│   ├── monthly_generator.py  # Injects monthly data into Word .docx templates
│   ├── financial_engine.py   # Calculates KES revenue, slippage gaps, & rolling target calibrations
│   ├── analytics.py          # Performs trend analysis, historical tracking, and deterministic risk verdicts
│   ├── contract_parser.py    # Extracts structured contract summaries
│   ├── document_parser.py    # Parses Project PoW plans and contractual correspondence
│   ├── progress_generator.py # Generates comprehensive management-level Word progress reports
│   └── schemas.py    # Pydantic data models (DailyReportSchema, etc.)
│   └── tests/        # Full flow, PoW, and format inspection test suite
└── frontend/         # Next.js (React/TypeScript) web application
```

### Backend Module Details

| Module | Responsibility |
|---|---|
| `main.py` | FastAPI app. Orchestrates pipelines, serves SSE generation streams, contract details, historical trends, and document caches. |
| `ai_client.py` | Manages service accounts in a round-robin pool. Fetches tokens and calls Vertex AI for vision and text generation. |
| `parser.py` | Converts PDFs to screenshots, filters out photo/scope pages, and calls vision endpoint using SHA256 fingerprint caching. |
| `aggregator.py` | Compiles daily logs into weekly data: adaptive labour matrix, weather condition grids, and professional works summaries. |
| `generator.py` | Injects data into templates and normalizes compiled document spacing to eliminate excessive indentations. |
| `financial_engine.py` | Calculates revenue ledgers and tracks slippage gaps against fixed and rolling target parameters. |
| `analytics.py` | Computes historical week trends, personnel averages, scatter data, and deterministic AI risk verdicts. |
| `document_parser.py` | AI-reviews Program of Works, letters, and schedules for contractual implications, milestones, and PM action items. |
| `progress_generator.py` | Exports in-depth monthly performance progress reports directly into styled Word documents. |

## Setup

### Prerequisites
- Python 3.11 (CRITICAL: 3.12, 3.13, and 3.14 are not supported due to dependency constraints)
- Node.js 18+
- Two Google Cloud service account JSON keys with Vertex AI access (one minimum, two recommended for load balancing).
- Word document templates in the `backend/` folder: `weekly_template.docx`, `monthly_template.docx`, and `monthly_report_template.docx`.

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
3. Use the **Upload** page to process daily reports, **Trends** to view live S-curves and recalibrations, and **Contract Reviews** to ingest scheduling documents.

## API Endpoints

### Compilation Pipeline
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/check-duplicate?title=<title>` | Detects if a weekly report already exists by title. |
| `POST` | `/api/generate-weekly-stream` | Accepts daily logs, streams upload → scan → generate phases via SSE. |
| `POST` | `/api/generate-monthly-stream` | Accepts weekly reports, validates chronology, and streams SSE progress. |
| `GET` | `/api/download-session/{session_id}` | Downloads the generated `.docx` report for the matching stream. |

### Analytics & Trends
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/trends` | Returns historical weekly compilation summaries. |
| `GET` | `/api/analytics/trends` | Returns combined weekly and daily trend records. |
| `GET` | `/api/analytics/financials` | Returns revenue earned, slippage gaps, ongoing targets, and weekly recalibrations. |
| `GET` | `/api/analytics/correlations` | Compiles correlation parameters for charts. |
| `GET` | `/api/analytics/insights` | Feeds current trends to Gemini to generate strategic SWOT reviews. |
| `GET` | `/api/generate-progress-report` | Compiles and streams a fully styled management-level Word progress report. |

### Contract Summary & Project Documents
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/contract-summary` | Returns parsed contract parameters and metadata. |
| `POST` | `/api/upload-document` | Uploads, parses, and AI-reviews contractual letters, schedules, and PoW PDFs. |
| `GET` | `/api/project-documents` | Retrieves all uploaded project documents and their structured review analysis. |
| `DELETE` | `/api/project-documents/{doc_id}` | Removes a project document and its parsed metadata. |

## Dependencies

- **Backend**: `fastapi`, `uvicorn`, `python-docx`, `PyMuPDF (fitz)`, `httpx`, `google-auth`, `pydantic`, `python-dotenv`
- **Frontend**: Next.js, React, TypeScript, Tailwind CSS, Lucide Icons, Recharts
