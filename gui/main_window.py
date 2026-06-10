from PySide6.QtWidgets import QMainWindow, QStackedWidget, QHBoxLayout, QWidget
from gui.components.sidebar import Sidebar
from gui.panels.mission_control import MissionControlPanel
from gui.panels.review_panel import ReviewPanel
from gui.services.tekira_service import TekiraService
from gui.workers.processing_worker import ProcessingWorker
from gui.animations import create_fade_in
from gui.models import DocumentJob

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Esperanto Repair Studio")
        self.resize(1100, 750)
        
        self.service = TekiraService()
        self.jobs = []
        self.workers = {}
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        
        self.sidebar = Sidebar()
        self.sidebar.item_selected.connect(self.navigate)
        
        self.stack = QStackedWidget()
        self.mission_control = MissionControlPanel(self)
        self.review_panel = ReviewPanel()
        
        self.mission_control.job_selected.connect(self.open_review)
        self.review_panel.back_requested.connect(lambda: self.navigate("dashboard"))
        
        self.stack.addWidget(self.mission_control)
        self.stack.addWidget(self.review_panel)
        
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack)
        
        self.anim, _ = create_fade_in(self, 300)
        self.anim.start()

    def navigate(self, view_id):
        if view_id == "dashboard":
            self.mission_control.update_jobs(self.jobs)
            self.stack.setCurrentWidget(self.mission_control)
        elif view_id == "learning":
            self.stack.setCurrentWidget(self.review_panel)
            
    def open_review(self, job: DocumentJob):
        if job.status == "completed" and job.result and job.result.manual_reviews_required > 0:
            self.review_panel.load_job(job)
            self.stack.setCurrentWidget(self.review_panel)

    def add_job(self, job: DocumentJob):
        self.jobs.append(job)
        self.mission_control.update_jobs(self.jobs)
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
        pass

    def on_job_progress(self, job_id, pct):
        for j in self.jobs:
            if j.id == job_id: j.progress = pct
        self.mission_control.update_jobs(self.jobs)

    def on_job_finished(self, job_id, result):
        for j in self.jobs:
            if j.id == job_id:
                j.status = "completed"
                j.progress = 100
                j.result = result
        self.mission_control.update_jobs(self.jobs)

    def on_job_error(self, job_id, err):
        for j in self.jobs:
            if j.id == job_id:
                j.status = "error"
                j.progress = 0
        self.mission_control.update_jobs(self.jobs)
