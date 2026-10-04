from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json

from variance_logic import (
    load_schedule, 
    save_weekly_snapshot, 
    get_snapshots_for_week
)

app = FastAPI(title="Standalone Variance Tracker API")

# Allow frontend to access this standalone server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SnapshotRequest(BaseModel):
    week_number: int
    report_date_str: str  # e.g., "2026-11-01" (Sunday's date)
    component: str
    task_name: str
    percentage: float
    notes: str = ""

@app.get("/api/variance/schedules/{component}")
def get_schedule(component: str):
    try:
        schedule = load_schedule(component)
        return schedule
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Schedule not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/variance/snapshot")
def save_snapshot(req: SnapshotRequest):
    try:
        record = save_weekly_snapshot(
            week_number=req.week_number,
            report_date_str=req.report_date_str,
            component=req.component,
            task_name=req.task_name,
            percentage=req.percentage,
            notes=req.notes
        )
        return {"status": "success", "record": record}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/variance/snapshots/{week_number}")
def get_snapshots(week_number: int):
    try:
        snapshots = get_snapshots_for_week(week_number)
        return snapshots
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting Standalone Variance Server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
