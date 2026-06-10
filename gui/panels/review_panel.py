from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class ReviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("Centro de Exploración Lingüística")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        title.setAlignment(Qt.AlignCenter)
        
        sub = QLabel("Aquí TEKIRA explicará sus heurísticas en Fase C4.")
        sub.setStyleSheet("color: #858585;")
        sub.setAlignment(Qt.AlignCenter)
        
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(sub)
        layout.addStretch()
