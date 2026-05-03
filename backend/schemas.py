from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class WorkBlock(BaseModel):
    block_name: str
    tasks: List[str]

class MaterialTest(BaseModel):
    test_type: str # e.g. "Concrete Cube Test" or "Slump Test"
    details: str # e.g. "12.3 N/mm2 at 7 days"
    location: str # e.g. "Block B1 Blinding"
    sn: Optional[str] = None # Serial Number if present

class SiteInstruction(BaseModel):
    ref_no: str = Field(..., alias="REF. NO")
    instruction_issued: str
    date: str
    issued_by: str = Field(..., alias="INSTRUCTIONS GIVEN BY")

class WeatherInfo(BaseModel):
    morning: str = Field(default="-")
    afternoon: str = Field(default="-")
    evening: str = Field(default="-")
    condition: str = Field(default="-")

class MachineryStatus(BaseModel):
    name: str
    qty: str
    status: str # e.g., "Working", "Idle", "Broken"

class DailyReportSchema(BaseModel):
    date: str # e.g., "Saturday 18th April 2026"
    day_of_week: Optional[str] = None # e.g., "Saturday"
    
    building_works: Dict[str, List[str]] = Field(default_factory=dict)
    general_works: List[str] = Field(default_factory=list)
    labour: Dict[str, Any] = Field(default_factory=dict) # e.g. {"Mason": "5", "Steel Fixer": {"Day": "5", "Night": "2"}}
    weather: WeatherInfo = Field(default_factory=WeatherInfo)
    
    materials_delivered: List[Dict[str, str]] = Field(default_factory=list) # [{Description, Quantity, Units}]
    machinery: List[MachineryStatus] = Field(default_factory=list)
    material_tests: List[MaterialTest] = Field(default_factory=list)
    instructions: List[SiteInstruction] = Field(default_factory=list)
    
    interns: Dict[str, str] = Field(default_factory=dict) # e.g. {"TVETS": "2"}
    security_status: str = Field(default="")
    health_safety_status: str = Field(default="")
    visitors: List[str] = Field(default_factory=list)
    challenges: List[str] = Field(default_factory=list)
    
    summary_of_works: Dict[str, str] = Field(default_factory=dict) # {Component: Description}
    confidence_score: float = Field(default=1.0)

class WeeklyReportSchema(BaseModel):
    reporting_period: str
    
    # Daily breakdowns (7 days)
    labour_daily: Dict[str, Dict[str, str]] = Field(default_factory=dict) # "YYYY-MM-DD": {"Category": "Value"}
    weather_daily: Dict[str, Dict[str, str]] = Field(default_factory=dict) # "YYYY-MM-DD": {"morning": "...", "afternoon": "...", "evening": "...", "condition": "...", "comments": "..."}
    
    # Aggregated/Snapshot sections
    insurances: List[Dict[str, str]] = Field(default_factory=list)
    materials_delivered: List[Dict[str, str]] = Field(default_factory=list)
    machinery: List[MachineryStatus] = Field(default_factory=list)
    instructions: List[SiteInstruction] = Field(default_factory=list)
    security_prose: str = ""
    security_issues: Dict[str, int] = Field(default_factory=dict) # e.g. {"theft": 1, "fight": 0}
    health_safety_prose: str = ""
    health_safety_issues: Dict[str, int] = Field(default_factory=dict) # e.g. {"incident": 2, "accident": 0}
    visitors_prose: str = ""
    challenges_prose: str = ""
    summary_to_date: Dict[str, str] = Field(default_factory=dict) # Section Q: {Block: Description}
    
    fingerprint: Optional[str] = None

class MonthlyReportSchema(BaseModel):
    title: str # e.g. "MONTHLY REPORT (MARCH 2026)"
    reporting_period: str
    time_elapsed: str
    pct_period: str
    pct_work: str
    
    # Weekly data for multi-table sections
    weekly_periods: List[str] = Field(default_factory=list)
    weekly_labour: List[Dict[str, Dict[str, str]]] = Field(default_factory=list) # List of 4-6 weekly matrices
    weekly_weather: List[List[Dict[str, str]]] = Field(default_factory=list) # List of 4-6 weekly grids
    weather_comments: List[str] = Field(default_factory=list)
    
    # Aggregated sections
    summary_to_date: Dict[str, str] = Field(default_factory=dict) # From the latest week
    materials_sum: Dict[str, Dict[str, Any]] = Field(default_factory=dict) # {Name: {qty: 0, unit: ""}}
    machinery: List[Dict[str, str]] = Field(default_factory=list) # {Name, Qty, Condition, Status}
    instructions: List[SiteInstruction] = Field(default_factory=list)
    
    # Aggregated prose
    health_safety: str = ""
    health_safety_issues: Dict[str, int] = Field(default_factory=dict)
    security: str = ""
    security_issues: Dict[str, int] = Field(default_factory=dict)
    challenges: str = ""
    
    visitors_prose: List[str] = Field(default_factory=list) # Not compiled into template, but kept in JSON
