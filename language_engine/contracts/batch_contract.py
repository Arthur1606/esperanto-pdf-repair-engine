from abc import ABC, abstractmethod
from typing import List

class BatchProcessor(ABC):
    @abstractmethod
    def process_queue(self, items: List[str]):
        pass
