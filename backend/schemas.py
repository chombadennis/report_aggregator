from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class WorkBlock(BaseModel):
    block_name: str
    tasks: List[str]

class MaterialTest(BaseModel):
    test_type: str # e.g. "Concrete Cube Test" or "Slump Test"
    details: str # e.g. "12.3 N/mm2 at 7 days"
    location: str # e.g. "Block B1 Blinding"

class DailyReportSchema(BaseModel):
    date: str
    building_works: Dict[str, List[str]] = Field(default_factory=dict)
    general_works: List[str] = Field(default_factory=list)
    labour: Dict[str, str] = Field(default_factory=dict)
    weather: Dict[str, str] = Field(default_factory=dict)
    materials_on_site: List[Dict[str, str]] = Field(default_factory=list)
    machinery: List[Dict[str, str]] = Field(default_factory=list)
    
    # NEW: Dynamic Material Tests
    material_tests: List[MaterialTest] = Field(default_factory=list)
    
    instructions: List[Dict[str, str]] = Field(default_factory=list)
    interns: Dict[str, str] = Field(default_factory=dict)
    security: str = Field(default="")
    health_safety: str = Field(default="")
    visitors: List[Dict[str, str]] = Field(default_factory=list)
    challenges: List[str] = Field(default_factory=list)
    confidence_score: float = Field(default=1.0, description="Confidence from 0.0 to 1.0")
