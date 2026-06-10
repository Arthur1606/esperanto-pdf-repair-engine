from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QGraphicsOpacityEffect
from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from gui.panels.dashboard_panel import DashboardPanel
from gui.panels.review_panel import ReviewPanel
from gui.panels.settings_panel import SettingsPanel
from gui.services.tekira_service import TekiraService
from gui.workers.processing_worker import ProcessingWorker
from gui.models import DocumentJob

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Esperanto Repair Studio - TEKIRA")
        self.resize(1000, 700)
        
        self.service = TekiraService()
        self.jobs = []
        self.workers = {}
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.dashboard = DashboardPanel(self)
        self.review = ReviewPanel(self)
        self.settings = SettingsPanel(self)
        
        self.tabs.addTab(self.dashboard, "Dashboard")
        self.tabs.addTab(self.review, "Revisión Manual")
        self.tabs.addTab(self.settings, "Configuración")
        
        # Fade in animation
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.anim = QPropertyAnimation(self.effect, b"opacity")
        self.anim.setDuration(800)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.start()

    def add_job(self, job: DocumentJob):
        self.jobs.append(job)
        self.dashboard.update_table(self.jobs)
        self.start_worker(job)

    def start_worker(self, job: DocumentJob):
        worker = ProcessingWorker(job, self.service)
        worker.started.connect(self.on_job_started)
        worker.progress_updated.connect(self.on_job_progress)
        worker.finished.connect(self.on_job_finished)
        worker.error.connect(self.on_job_error)
        self.workers[job.id] = worker
        worker.start()

    def on_job_started(self, job_id):
        for j in self.jobs:
            if j.id == job_id:
                j.status = "processing"
                break
        self.dashboard.update_table(self.jobs)

    def on_job_progress(self, job_id, pct):
        for j in self.jobs:
            if j.id == job_id:
                j.progress = pct
                break
        self.dashboard.update_table(self.jobs)

    def on_job_finished(self, job_id, result):
        for j in self.jobs:
            if j.id == job_id:
                j.status = "completed"
                j.progress = 100
                break
        self.dashboard.update_table(self.jobs)

    def on_job_error(self, job_id, err):
        for j in self.jobs:
            if j.id == job_id:
                j.status = "error"
                j.progress = 0
                break
        self.dashboard.update_table(self.jobs)
