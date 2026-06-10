from dataclasses import dataclass
from typing import List
from .review_item import ReviewItem

@dataclass
class RepairResult:
    success: bool
    manual_reviews_required: int
    items: List[ReviewItem]
