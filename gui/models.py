from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class DocumentJob:
    id: str
    filepath: str
    status: str
    progress: int

@dataclass
class ReviewItem:
    original_word: str
    context: str
    candidates: List[Dict[str, float]]

@dataclass
class RepairResult:
    success: bool
    manual_reviews_required: int
    items: List[ReviewItem]
