from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor
from gui.models import DocumentJob, DocumentSourceType

class DocumentCard(QWidget):
    def __init__(self, job: DocumentJob, parent=None):
        super().__init__(parent)
        self.job = job
        self.setObjectName("DocumentCard")
        self.setFixedHeight(120)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        h_layout = QHBoxLayout()
        icon = "📄" if job.source_type == DocumentSourceType.PDF else "📝"
        title = QLabel(f"{icon} {job.filepath.split('/')[-1] if job.filepath else 'Portapapeles'}")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.status = QLabel(self.get_status_text())
        self.status.setAlignment(Qt.AlignRight)
        
        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(self.status)
        layout.addLayout(h_layout)
        
        # Progress Bar Placeholder
        self.progress_bg = QWidget()
        self.progress_bg.setFixedHeight(4)
        self.progress_bg.setStyleSheet("background-color: #333; border-radius: 2px;")
        
        layout.addStretch()
        layout.addWidget(self.progress_bg)
        
    def get_status_text(self):
        if self.job.status == "processing": return "⏳ Procesando..."
        if self.job.status == "completed": return "✅ Listo"
        if self.job.status == "error": return "❌ Error"
        return "Pendiente"
        
    def update_job(self, job: DocumentJob):
        self.job = job
        self.status.setText(self.get_status_text())
        # TODO: Animar ancho de progress bar interno
