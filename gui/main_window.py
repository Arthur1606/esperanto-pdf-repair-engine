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
from gui.components.tekira_aura import TekiraAura
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
        
        # ── Atmosphere (Floats behind everything) ─────
        self.aura = TekiraAura(self)
        self.aura.resize(1200, 800)
        self.aura.show()
        self.aura.lower()

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

        self.mission_control = MissionControlPanel(self)
        self.mission_control.job_selected.connect(self.open_review)
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.mission_control)

        # ── Review Panel (Floats on top of Mission Control)
        # Parent it to main_container so it overlays the dashboard
        self.review_panel = ReviewPanel(self.main_container)
        self.review_panel.hide()
        self.review_panel.back_requested.connect(lambda: self.navigate("dashboard"))

        # ── Genesis Overlay (Floats on top of everything)
        self.genesis_overlay = GenesisOverlay(self)
        self.genesis_overlay.resize(1200, 800)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.genesis_overlay.resize(self.size())
        self.aura.resize(self.size())
        # The review panel only covers the mission control area, but let's 
        # make it cover the same space. Actually, letting it cover the whole app
        # creates a better modal feel, or just the mission control area.
        # Let's make it cover the right side.
        sidebar_w = self.sidebar.width()
        self.review_panel.setGeometry(sidebar_w, 0, self.width() - sidebar_w, self.height())

    def showEvent(self, event):
        super().showEvent(event)
        # Delay welcome sequence to allow window resize to stabilize (prevents text jumping)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(200, lambda: self.genesis_overlay.start(
            main_container=self.main_container,
            on_complete=None
        ))

    def navigate(self, view_id: str):
        if view_id == "dashboard":
            from PySide6.QtWidgets import QGraphicsBlurEffect
            # Remove blur from mission_control
            self.mission_control.setGraphicsEffect(None)
            self.review_panel.hide()
        else:
            # We don't have other views yet, but they would go here
            pass

    def open_review(self, job: DocumentJob):
        # 1. Apply strong blur to mission control
        from PySide6.QtWidgets import QGraphicsBlurEffect
        blur = QGraphicsBlurEffect(self.mission_control)
        blur.setBlurRadius(20)
        self.mission_control.setGraphicsEffect(blur)
        
        # 2. Show the floating Review Panel
        # Force a geometry update before showing
        sidebar_w = self.sidebar.width()
        self.review_panel.setGeometry(sidebar_w, 0, self.width() - sidebar_w, self.height())
        self.review_panel.raise_()
        self.review_panel.show()
        
        # 3. Load job
        self.review_panel.load_job(job)

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
