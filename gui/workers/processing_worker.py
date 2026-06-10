from PySide6.QtCore import QThread, Signal
from gui.models import DocumentJob, RepairResult
from gui.services.tekira_service import TekiraService
import logging
import time

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
            t0 = time.time()
            self.started.emit(self.job.id)
            self.progress_updated.emit(self.job.id, 10)
            
            # Real execution
            result = self.service.analyze_document(self.job)
            
            self.progress_updated.emit(self.job.id, 90)
            
            dt = time.time() - t0
            logger.info(f"Job {self.job.id} done in {dt:.2f}s")
            
            self.progress_updated.emit(self.job.id, 100)
            self.finished.emit(self.job.id, result)
        except Exception as e:
            logger.error(f"Worker Error: {e}")
            self.error.emit(self.job.id, str(e))
