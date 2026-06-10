from abc import ABC, abstractmethod

class TekiraGUIListener(ABC):
    @abstractmethod
    def on_progress(self, percentage: int):
        pass
