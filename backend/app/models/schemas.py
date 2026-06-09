from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class FontAuditSchema(BaseModel):
    id: str
    font_name: str
    page_count: int
    unicode_support: bool
    esperanto_support: bool

    class Config:
        orm_mode = True

class CorrectionSchema(BaseModel):
    id: str
    page_num: int
    original_string: str
    suggested_string: str
    confidence: float
    status: str
    error_type: str
    bounding_box: Optional[Dict[str, float]]

    class Config:
        orm_mode = True

class DocumentSchema(BaseModel):
    id: str
    filename: str
    status: str
    unicode_score: Optional[float]
    font_score: Optional[float]
    text_validity_score: Optional[float]
    overall_score: Optional[float]
    debug_info: Optional[Dict] = None
    fonts: List[FontAuditSchema] = []
    corrections: List[CorrectionSchema] = []

    class Config:
        orm_mode = True

class ProjectSchema(BaseModel):
    id: str
    name: str
    status: str
    created_at: datetime
    documents: List[DocumentSchema] = []

    class Config:
        orm_mode = True

class ProjectCreate(BaseModel):
    name: str
