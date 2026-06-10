from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class ReviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("🛠 Manual Review Placeholder")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
from PySide6.QtCore import Qt
