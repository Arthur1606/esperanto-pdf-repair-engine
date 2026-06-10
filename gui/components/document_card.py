"""
DocumentCard — Premium editorial card for document jobs.
Features spatial levitation on hover.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QColor, QCursor
from gui.models import DocumentJob, DocumentSourceType
from gui.styles.design_system import TDS


class DocumentCard(QWidget):
    clicked = Signal(object)

    def __init__(self, job: DocumentJob, parent=None):
        super().__init__(parent)
        self.job = job
        self.setObjectName("DocumentCard")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(130)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(TDS.SPACE_LG, TDS.SPACE_LG, TDS.SPACE_LG, TDS.SPACE_LG)
        layout.setSpacing(TDS.SPACE_SM)

        # ── Header Row ─────────────────────────────────
        header = QHBoxLayout()

        # Type badge
        type_text = "PDF" if job.source_type == DocumentSourceType.PDF else (
            "TXT" if job.source_type == DocumentSourceType.TXT else "CLIP"
        )
        badge = QLabel(type_text)
        badge.setFixedWidth(42)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            f"background-color: {TDS.GOLD_SUBTLE}; color: {TDS.GOLD}; "
            f"font-size: {TDS.FONT_SMALL}px; font-weight: 700; "
            f"border-radius: 4px; padding: 3px 0px;"
        )

        name = job.filepath.split("/")[-1] if job.filepath else "Portapapeles"
        title = QLabel(name)
        title.setObjectName("CardTitle")

        header.addWidget(badge)
        header.addSpacing(8)
        header.addWidget(title)
        header.addStretch()

        self.status_label = QLabel(self._status_text())
        self.status_label.setObjectName("CardStatus")
        self._apply_status_color()
        header.addWidget(self.status_label)

        layout.addLayout(header)
        layout.addStretch()

        # ── Progress Bar ───────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("CardProgress")
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(job.progress)
        layout.addWidget(self.progress_bar)

        self._shadow_applied = False

    def showEvent(self, event):
        super().showEvent(event)
        # Apply massive, diffuse shadow only once layout is established
        if not self._shadow_applied:
            self.shadow = QGraphicsDropShadowEffect(self)
            self.shadow.setBlurRadius(30)
            self.shadow.setOffset(0, 6)
            self.shadow.setColor(QColor(0, 0, 0, 45)) # Premium visible shadow (18% alpha)
            self.setGraphicsEffect(self.shadow)
            self._shadow_applied = True

            # Pre-create animations for Levitation (shadow only to prevent layout fight)
            self._anim_shadow_blur = QPropertyAnimation(self.shadow, b"blurRadius")
            self._anim_shadow_blur.setDuration(180)
            self._anim_shadow_blur.setEasingCurve(QEasingCurve.OutCubic)

            self._anim_shadow_offset = QPropertyAnimation(self.shadow, b"yOffset")
            self._anim_shadow_offset.setDuration(180)
            self._anim_shadow_offset.setEasingCurve(QEasingCurve.OutCubic)

    def enterEvent(self, event):
        super().enterEvent(event)
        if hasattr(self, 'shadow'):
            self._anim_shadow_blur.stop()
            self._anim_shadow_blur.setStartValue(self.shadow.blurRadius())
            self._anim_shadow_blur.setEndValue(50)
            self._anim_shadow_blur.start()

            self._anim_shadow_offset.stop()
            self._anim_shadow_offset.setStartValue(self.shadow.yOffset())
            self._anim_shadow_offset.setEndValue(14)
            self._anim_shadow_offset.start()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if hasattr(self, 'shadow'):
            self._anim_shadow_blur.stop()
            self._anim_shadow_blur.setStartValue(self.shadow.blurRadius())
            self._anim_shadow_blur.setEndValue(30)
            self._anim_shadow_blur.start()

            self._anim_shadow_offset.stop()
            self._anim_shadow_offset.setStartValue(self.shadow.yOffset())
            self._anim_shadow_offset.setEndValue(6)
            self._anim_shadow_offset.start()

    def _status_text(self) -> str:
        s = self.job.status
        if s == "processing":
            return "Procesando..."
        if s == "completed":
            rev = self.job.result.manual_reviews_required if self.job.result else 0
            return f"Listo · {rev} rev" if rev else "Listo"
        if s == "error":
            return "Error"
        return "En espera"

    def _apply_status_color(self):
        s = self.job.status
        color = TDS.TEXT_SECONDARY
        if s == "completed":
            color = TDS.SUCCESS
        elif s == "error":
            color = TDS.DANGER
        elif s == "processing":
            color = TDS.GOLD
        self.status_label.setStyleSheet(
            f"color: {color}; font-size: {TDS.FONT_CAPTION}px; font-weight: 500;"
        )

    def update_job(self, job: DocumentJob):
        self.job = job
        self.status_label.setText(self._status_text())
        self._apply_status_color()
        self.progress_bar.setValue(job.progress)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.job)
        super().mousePressEvent(event)
