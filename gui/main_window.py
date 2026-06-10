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
from gui.components.splash_screen import SplashScreen
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

        # ── Root Stack: Splash over Main ───────────────
        self.root_stack = QStackedWidget()
        self.setCentralWidget(self.root_stack)

        # ── Splash ─────────────────────────────────────
        self.splash = SplashScreen()
        self.root_stack.addWidget(self.splash)

        # ── Main Content ───────────────────────────────
        self.main_container = QWidget()
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

        self.root_stack.addWidget(self.main_container)

        # Start on splash
        self.root_stack.setCurrentWidget(self.splash)

    def showEvent(self, event):
        super().showEvent(event)
        # Trigger splash animation after window is visible
        self.splash.start(self._transition_to_main)

    def _transition_to_main(self):
        """Fade the main UI in after splash dissolves."""
        self.root_stack.setCurrentWidget(self.main_container)

        self._main_effect = QGraphicsOpacityEffect(self.main_container)
        self.main_container.setGraphicsEffect(self._main_effect)

        self._main_fade = QPropertyAnimation(self._main_effect, b"opacity")
        self._main_fade.setDuration(TDS.ANIM_SLOW)
        self._main_fade.setStartValue(0)
        self._main_fade.setEndValue(1)
        self._main_fade.setEasingCurve(QEasingCurve.OutCubic)
        self._main_fade.start()

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
