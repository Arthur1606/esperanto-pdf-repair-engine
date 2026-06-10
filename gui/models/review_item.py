from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ReviewItem:
    original_word: str
    context: str
    candidates: List[Dict[str, float]]
