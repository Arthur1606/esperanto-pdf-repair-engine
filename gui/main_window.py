from PySide6.QtWidgets import QMainWindow, QStackedWidget, QHBoxLayout, QWidget
from gui.components.sidebar import Sidebar
from gui.panels.mission_control import MissionControlPanel
from gui.panels.review_panel import ReviewPanel
from gui.services.tekira_service import TekiraService
from gui.animations import create_fade_in
from gui.models import DocumentJob

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Esperanto Repair Studio")
        self.resize(1100, 750)
        
        self.service = TekiraService()
        self.jobs = []
        
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
        
        self.stack.addWidget(self.mission_control)
        self.stack.addWidget(self.review_panel)
        
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack)
        
        self.anim, _ = create_fade_in(self, 300)
        self.anim.start()

    def navigate(self, view_id):
        if view_id == "dashboard": self.stack.setCurrentWidget(self.mission_control)
        elif view_id == "learning": self.stack.setCurrentWidget(self.review_panel)
        
    def add_job(self, job: DocumentJob):
        self.jobs.append(job)
        self.mission_control.update_jobs(self.jobs)
        # Real processing connection will go here via worker
