from abc import ABC, abstractmethod

class DocumentExporter(ABC):
    @abstractmethod
    def export(self, content: str, target_path: str) -> bool:
        pass
