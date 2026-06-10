from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt

class DashboardPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        self.title = QLabel("📄 Dashboard de Archivos")
        self.title.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Origen", "Estado", "Progreso", "Alertas", "Acción"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.btn_process = QPushButton("▶ Procesar Todo")
        
        layout.addWidget(self.title)
        layout.addWidget(self.table)
        layout.addWidget(self.btn_process)
