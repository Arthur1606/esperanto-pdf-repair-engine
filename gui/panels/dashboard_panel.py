from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit, QFileDialog
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QBrush
from gui.models import DocumentJob, DocumentSourceType
import uuid

class DashboardPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        self.title = QLabel("📄 Dashboard de Archivos")
        self.title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        layout.addWidget(self.title)

        # Top area: Drag & Drop + Clipboard
        top_layout = QHBoxLayout()
        
        # Left: Drop Zone
        self.drop_label = QLabel("Arrastra PDF / TXT aquí\no haz clic para seleccionar")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #3e3e42;
                border-radius: 8px;
                background-color: #252526;
                color: #858585;
                font-size: 14px;
                padding: 40px;
            }
            QLabel:hover {
                border-color: #007acc;
                background-color: #2d2d2d;
            }
        """)
        top_layout.addWidget(self.drop_label, 1)

        # Right: Clipboard
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("O pega texto plano aquí...")
        self.text_input.setStyleSheet("background-color: #252526; border: 1px solid #3e3e42; border-radius: 8px; padding: 10px;")
        top_layout.addWidget(self.text_input, 1)

        layout.addLayout(top_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_load_file = QPushButton("📁 Cargar Archivo")
        self.btn_process_text = QPushButton("▶ Procesar Texto Pegado")
        btn_layout.addWidget(self.btn_load_file)
        btn_layout.addWidget(self.btn_process_text)
        layout.addLayout(btn_layout)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Origen", "Tipo", "Estado", "Progreso", "Acción"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.btn_load_file.clicked.connect(self._select_file)
        self.btn_process_text.clicked.connect(self._process_clipboard)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath.lower().endswith(('.pdf', '.txt')):
                self.add_job_from_file(filepath)

    def _select_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo", "", "Documentos (*.pdf *.txt)")
        if filepath:
            self.add_job_from_file(filepath)

    def _process_clipboard(self):
        text = self.text_input.toPlainText()
        if text.strip():
            job = DocumentJob(id=str(uuid.uuid4()), source_type=DocumentSourceType.CLIPBOARD, filepath=None, content=text, status="idle", progress=0)
            self.parent().parent().parent().add_job(job) # Access main window
            self.text_input.clear()

    def add_job_from_file(self, filepath):
        stype = DocumentSourceType.PDF if filepath.lower().endswith('.pdf') else DocumentSourceType.TXT
        job = DocumentJob(id=str(uuid.uuid4()), source_type=stype, filepath=filepath, content=None, status="idle", progress=0)
        self.parent().parent().parent().add_job(job)

    def update_table(self, jobs):
        self.table.setRowCount(len(jobs))
        for row, job in enumerate(jobs):
            name = job.filepath.split('/')[-1] if job.filepath else "Portapapeles"
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(job.source_type.value.upper()))
            
            status_item = QTableWidgetItem(job.status)
            if job.status == "error": status_item.setForeground(QBrush(QColor("#f14c4c")))
            elif job.status == "completed": status_item.setForeground(QBrush(QColor("#89d185")))
            
            self.table.setItem(row, 2, status_item)
            self.table.setItem(row, 3, QTableWidgetItem(f"{job.progress}%"))
            self.table.setItem(row, 4, QTableWidgetItem("---"))
