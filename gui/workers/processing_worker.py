from PySide6.QtCore import QThread, Signal
from gui.models import DocumentJob, RepairResult
from gui.services.tekira_service import TekiraService
import logging

logger = logging.getLogger("studio.worker")

class ProcessingWorker(QThread):
    started = Signal(str)
    progress_updated = Signal(str, int)
    finished = Signal(str, object)
    error = Signal(str, str)

    def __init__(self, job: DocumentJob, service: TekiraService):
        super().__init__()
        self.job = job
        self.service = service

    def run(self):
        try:
            self.started.emit(self.job.id)
            for i in range(1, 101, 10):
                self.progress_updated.emit(self.job.id, i)
                self.msleep(100) # Simular auditoría
            
            result = self.service.analyze_document(self.job)
            self.progress_updated.emit(self.job.id, 100)
            self.finished.emit(self.job.id, result)
        except Exception as e:
            logger.error(f"Error en worker: {e}")
            self.error.emit(self.job.id, str(e))
