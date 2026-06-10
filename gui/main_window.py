from PySide6.QtWidgets import QMainWindow, QTabWidget
from gui.panels.dashboard_panel import DashboardPanel
from gui.panels.review_panel import ReviewPanel
from gui.panels.settings_panel import SettingsPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Esperanto Repair Studio - Powered by TEKIRA")
        self.resize(900, 600)
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.dashboard = DashboardPanel()
        self.review = ReviewPanel()
        self.settings = SettingsPanel()
        
        self.tabs.addTab(self.dashboard, "Dashboard")
        self.tabs.addTab(self.review, "Revisión Manual")
        self.tabs.addTab(self.settings, "Configuración")
