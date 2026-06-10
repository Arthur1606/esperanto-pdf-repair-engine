"""
MainWindow — Esperanto Language Suite
Orchestrates splash → main UI transition with sidebar + stacked content.
"""
from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QHBoxLayout, QVBoxLayout, QWidget,
    QGraphicsOpacityEffect
)
from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from gui.components.sidebar import Sidebar
from gui.components.genesis_overlay import GenesisOverlay
from gui.panels.mission_control import MissionControlPanel
from gui.panels.review_panel import ReviewPanel
from gui.services.tekira_service import TekiraService
from gui.workers.processing_worker import ProcessingWorker
from gui.styles.design_system import TDS
from gui.models import DocumentJob


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Esperanto Language Suite")
        self.resize(1200, 800)

        self.service = TekiraService()
        self.jobs = []
        self.workers = {}

        # ── Main Content Container ──────────────────────
        self.main_container = QWidget()
        self.setCentralWidget(self.main_container)
        main_layout = QHBoxLayout(self.main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.item_selected.connect(self.navigate)

        self.content_stack = QStackedWidget()
        self.mission_control = MissionControlPanel(self)
        self.review_panel = ReviewPanel()

        self.mission_control.job_selected.connect(self.open_review)
        self.review_panel.back_requested.connect(lambda: self.navigate("dashboard"))

        self.content_stack.addWidget(self.mission_control)
        self.content_stack.addWidget(self.review_panel)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_stack)

        # ── Genesis Overlay (Floats on top) ───────────
        self.genesis_overlay = GenesisOverlay(self)
        self.genesis_overlay.resize(1200, 800)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.genesis_overlay.resize(self.size())

    def showEvent(self, event):
        super().showEvent(event)
        # Start Structural Constancy Sequence
        self.genesis_overlay.start(
            target_widget=self.sidebar.brand_label,
            main_container=self.main_container,
            on_complete=None
        )

    def navigate(self, view_id: str):
        if view_id == "dashboard":
            self.mission_control.update_jobs(self.jobs)
            self.content_stack.setCurrentWidget(self.mission_control)
        elif view_id == "learning":
            self.content_stack.setCurrentWidget(self.review_panel)

    def open_review(self, job: DocumentJob):
        if (
            job.status == "completed"
            and job.result
            and job.result.manual_reviews_required > 0
        ):
            self.review_panel.load_job(job)
            self.content_stack.setCurrentWidget(self.review_panel)

    def add_job(self, job: DocumentJob):
        self.jobs.append(job)
        self.mission_control.update_jobs(self.jobs)
        self._start_worker(job)

    def _start_worker(self, job: DocumentJob):
        worker = ProcessingWorker(job, self.service)
        worker.started.connect(self._on_job_started)
        worker.progress_updated.connect(self._on_job_progress)
        worker.finished.connect(self._on_job_finished)
        worker.error.connect(self._on_job_error)
        self.workers[job.id] = worker
        worker.start()

    def _on_job_started(self, job_id):
        for j in self.jobs:
            if j.id == job_id:
                j.status = "processing"
        self.mission_control.update_jobs(self.jobs)

    def _on_job_progress(self, job_id, pct):
        for j in self.jobs:
            if j.id == job_id:
                j.progress = pct
        self.mission_control.update_jobs(self.jobs)

    def _on_job_finished(self, job_id, result):
        for j in self.jobs:
            if j.id == job_id:
                j.status = "completed"
                j.progress = 100
                j.result = result
        self.mission_control.update_jobs(self.jobs)

    def _on_job_error(self, job_id, err):
        for j in self.jobs:
            if j.id == job_id:
                j.status = "error"
                j.progress = 0
        self.mission_control.update_jobs(self.jobs)
