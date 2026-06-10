from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QGridLayout, QPushButton, QTextEdit
from PySide6.QtCore import Qt
from gui.components.document_card import DocumentCard
from gui.models import DocumentJob, DocumentSourceType
import uuid

class MissionControlPanel(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Hero Section
        hero = QWidget()
        hero.setObjectName("HeroSection")
        hero_layout = QVBoxLayout(hero)
        title = QLabel("TEKIRA | Centro de Operaciones")
        title.setStyleSheet("font-size: 28px; font-weight: 800; color: #ffffff;")
        subtitle = QLabel("Motor lingüístico en espera. 0 Documentos procesados hoy.")
        subtitle.setStyleSheet("font-size: 14px; color: #858585;")
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)
        layout.addWidget(hero)
        
        # Metrics Row
        metrics = QHBoxLayout()
        metrics.addWidget(self._create_metric("Automatización", "0%", "Tasa TEKIRA"))
        metrics.addWidget(self._create_metric("Por Revisar", "0", "Ambigüedades"))
        metrics.addWidget(self._create_metric("Tiempo Ahorrado", "0h 0m", "Frente a edición manual"))
        layout.addLayout(metrics)
        
        # Input Area (Drag Drop + Text)
        input_layout = QHBoxLayout()
        self.drop_area = QLabel("Arrastra Documentos Aquí\n(PDF, TXT)")
        self.drop_area.setObjectName("DropArea")
        self.drop_area.setAlignment(Qt.AlignCenter)
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("O pega texto plano aquí...")
        self.text_input.setObjectName("TextInput")
        
        input_layout.addWidget(self.drop_area)
        input_layout.addWidget(self.text_input)
        layout.addLayout(input_layout)
        
        btn = QPushButton("Procesar Portapapeles")
        btn.setObjectName("PrimaryBtn")
        btn.clicked.connect(self._process_clipboard)
        layout.addWidget(btn, 0, Qt.AlignRight)
        
        # Cards Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        self.cards_container = QWidget()
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(15)
        scroll.setWidget(self.cards_container)
        
        layout.addWidget(QLabel("Documentos Recientes"), 0, Qt.AlignLeft)
        layout.addWidget(scroll)

    def _create_metric(self, title, value, desc):
        w = QWidget()
        w.setObjectName("MetricCard")
        l = QVBoxLayout(w)
        lt = QLabel(title)
        lt.setStyleSheet("color: #858585; font-size: 12px; font-weight: 600;")
        lv = QLabel(value)
        lv.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: 800;")
        ld = QLabel(desc)
        ld.setStyleSheet("color: #5E5CE6; font-size: 11px;")
        l.addWidget(lt)
        l.addWidget(lv)
        l.addWidget(ld)
        return w

    def _process_clipboard(self):
        text = self.text_input.toPlainText()
        if text.strip():
            job = DocumentJob(id=str(uuid.uuid4()), source_type=DocumentSourceType.CLIPBOARD, filepath=None, content=text, status="idle", progress=0)
            self.main_window.add_job(job)
            self.text_input.clear()

    def update_jobs(self, jobs):
        # Clear layout
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        row, col = 0, 0
        for job in reversed(jobs): # Show newest first
            card = DocumentCard(job)
            self.cards_layout.addWidget(card, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1
