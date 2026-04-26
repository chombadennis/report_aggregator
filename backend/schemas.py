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
