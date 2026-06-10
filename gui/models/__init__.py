from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional

class DocumentSourceType(Enum):
    PDF = "pdf"
    TXT = "txt"
    CLIPBOARD = "clipboard"

@dataclass
class DocumentJob:
    id: str
    source_type: DocumentSourceType
    filepath: Optional[str]
    content: Optional[str]
    status: str
    progress: int
    result: Optional['RepairResult'] = None

@dataclass
class ReviewItem:
    original_word: str
    context: str
    candidates: List[Dict[str, float]]
    resolved_word: Optional[str] = None
    is_resolved: bool = False

@dataclass
class RepairResult:
    success: bool
    manual_reviews_required: int
    items: List[ReviewItem]
