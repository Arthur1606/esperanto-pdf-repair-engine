"""
Mission Control Panel — Editorial Dashboard
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QGridLayout, QPushButton, QTextEdit, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from gui.components.document_card import DocumentCard
from gui.models import DocumentJob, DocumentSourceType
from gui.styles.design_system import TDS
import uuid


class MissionControlPanel(QWidget):
    job_selected = Signal(object)

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(32)

        # ── Editorial Header (Minimalist running signature) ──
        header_bar = QHBoxLayout()
        
        brand_sig = QLabel("ESPERANTO LANGUAGE SUITE")
        brand_sig.setStyleSheet(
            f"font-size: 10px; "
            f"font-weight: 700; "
            f"color: {TDS.TEXT_SECONDARY}; "
            f"letter-spacing: 3px;"
        )
        
        tagline = QLabel("powered by TEKIRA")
        tagline.setStyleSheet(
            f"font-size: 10px; "
            f"font-weight: 500; "
            f"color: {TDS.GOLD}; "
            f"letter-spacing: 1px;"
        )
        
        header_bar.addWidget(brand_sig)
        header_bar.addStretch()
        header_bar.addWidget(tagline)
        layout.addLayout(header_bar)

        # ── Metrics Row ────────────────────────────────
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(TDS.SPACE_MD)
        self.m_docs = self._create_metric("Documentos", "0", "Procesados")
        self.m_rev = self._create_metric("Revisiones", "0", "Pendientes")
        self.m_auto = self._create_metric("Automatización", "—", "Tasa TEKIRA")
        metrics_row.addWidget(self.m_docs)
        metrics_row.addWidget(self.m_rev)
        metrics_row.addWidget(self.m_auto)
        layout.addLayout(metrics_row)

        # ── Input Area ─────────────────────────────────
        input_layout = QHBoxLayout()
        input_layout.setSpacing(TDS.SPACE_MD)

        self.drop_area = QLabel("Arrastra documentos aquí\nPDF · TXT")
        self.drop_area.setObjectName("DropArea")
        self.drop_area.setAlignment(Qt.AlignCenter)
        self.drop_area.setMinimumHeight(120)

        # Physical shadow for Drop Area
        da_shadow = QGraphicsDropShadowEffect(self.drop_area)
        da_shadow.setBlurRadius(25)
        da_shadow.setOffset(0, 5)
        da_shadow.setColor(QColor(0, 0, 0, 20))
        self.drop_area.setGraphicsEffect(da_shadow)

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("O pega texto aquí...")
        self.text_input.setObjectName("TextInput")
        self.text_input.setMinimumHeight(120)

        # Physical shadow for Text Input
        ti_shadow = QGraphicsDropShadowEffect(self.text_input)
        ti_shadow.setBlurRadius(25)
        ti_shadow.setOffset(0, 5)
        ti_shadow.setColor(QColor(0, 0, 0, 20))
        self.text_input.setGraphicsEffect(ti_shadow)

        input_layout.addWidget(self.drop_area, 1)
        input_layout.addWidget(self.text_input, 1)
        layout.addLayout(input_layout)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn = QPushButton("Analizar texto")
        btn.setObjectName("PrimaryBtn")
        btn.clicked.connect(self._process_clipboard)
        btn_row.addWidget(btn)
        layout.addLayout(btn_row)

        # ── Section Label ──────────────────────────────
        section = QLabel("DOCUMENTOS RECIENTES")
        section.setObjectName("SectionLabel")
        layout.addWidget(section)

        # ── Cards Scroll Area ──────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent;")
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(TDS.SPACE_LG)
        self.cards_layout.setContentsMargins(16, 16, 16, 16)
        scroll.setWidget(self.cards_container)

        # Empty state
        self.empty_label = QLabel("Aún no hay documentos.\nArrastra un archivo o pega texto para comenzar.")
        self.empty_label.setObjectName("EmptyState")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.cards_layout.addWidget(self.empty_label, 0, 0, 1, 3, Qt.AlignCenter)

        layout.addWidget(scroll)

    def _create_metric(self, title: str, value: str, desc: str) -> QWidget:
        w = QWidget()
        w.setObjectName("MetricCard")
        w.setAttribute(Qt.WA_StyledBackground, True)
        
        # Physical shadow for Metric Cards
        shadow = QGraphicsDropShadowEffect(w)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 15))
        w.setGraphicsEffect(shadow)

        l = QVBoxLayout(w)
        l.setSpacing(4)

        lt = QLabel(title)
        lt.setObjectName("MetricLabel")

        lv = QLabel(value)
        lv.setObjectName("MetricValue")

        ld = QLabel(desc)
        ld.setObjectName("MetricDesc")

        l.addWidget(lt)
        l.addWidget(lv)
        l.addWidget(ld)
        w.val_label = lv
        return w

    def _process_clipboard(self):
        text = self.text_input.toPlainText()
        if text.strip():
            job = DocumentJob(
                id=str(uuid.uuid4()),
                source_type=DocumentSourceType.CLIPBOARD,
                filepath=None,
                content=text,
                status="idle",
                progress=0,
            )
            self.main_window.add_job(job)
            self.text_input.clear()

    def update_jobs(self, jobs):
        # Clear
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not jobs:
            self.empty_label = QLabel(
                "Aún no hay documentos.\nArrastra un archivo o pega texto para comenzar."
            )
            self.empty_label.setObjectName("EmptyState")
            self.empty_label.setAlignment(Qt.AlignCenter)
            self.cards_layout.addWidget(self.empty_label, 0, 0, 1, 3, Qt.AlignCenter)
            return

        row, col = 0, 0
        total_rev = 0
        for job in reversed(jobs):
            card = DocumentCard(job)
            card.clicked.connect(self.job_selected.emit)
            self.cards_layout.addWidget(card, row, col)
            if job.result:
                total_rev += job.result.manual_reviews_required
            col += 1
            if col > 2:
                col = 0
                row += 1

        self.m_docs.val_label.setText(str(len(jobs)))
        self.m_rev.val_label.setText(str(total_rev))
