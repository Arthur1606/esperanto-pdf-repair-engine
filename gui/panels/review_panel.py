"""
Review Panel — Centro de Exploración Lingüística
The emotional heart of Esperanto Language Suite.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from gui.models import DocumentJob, ReviewItem
from gui.styles.design_system import TDS


class CandidateButton(QPushButton):
    def __init__(self, text: str, score: float):
        super().__init__(text)
        self.setObjectName("CandidateBtn")
        self.score = score
        pct = score * 100
        self.setToolTip(f"Confianza de TEKIRA: {pct:.0f}%")


class ReviewPanel(QWidget):
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.job = None
        self.current_idx = 0
        self.items = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            TDS.SPACE_XXL + 20, TDS.SPACE_XXL, TDS.SPACE_XXL + 20, TDS.SPACE_XL
        )
        layout.setSpacing(TDS.SPACE_LG)

        # ── Header ─────────────────────────────────────
        header = QHBoxLayout()
        btn_back = QPushButton("← Dashboard")
        btn_back.setObjectName("SecondaryBtn")
        btn_back.clicked.connect(self.back_requested.emit)

        self.lbl_progress = QLabel("0 / 0")
        self.lbl_progress.setStyleSheet(
            f"color: {TDS.TEXT_SECONDARY}; font-weight: 600; font-size: {TDS.FONT_BODY}px;"
        )

        header.addWidget(btn_back)
        header.addStretch()
        header.addWidget(self.lbl_progress)
        layout.addLayout(header)

        # ── Centered Review Card ───────────────────────
        self.main_area = QWidget()
        self.main_area.setObjectName("ReviewCard")
        main_layout = QVBoxLayout(self.main_area)
        main_layout.setSpacing(TDS.SPACE_LG)
        main_layout.setContentsMargins(
            TDS.SPACE_XXL, TDS.SPACE_XXL, TDS.SPACE_XXL, TDS.SPACE_XL
        )

        # Context
        self.lbl_context = QLabel()
        self.lbl_context.setObjectName("ReviewContext")
        self.lbl_context.setWordWrap(True)
        self.lbl_context.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_context)

        # Target Word (the star of the show)
        self.lbl_target = QLabel()
        self.lbl_target.setObjectName("ReviewTarget")
        self.lbl_target.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_target)

        main_layout.addSpacing(8)

        # Explanation
        expl_box = QWidget()
        expl_box.setObjectName("ExplanationBox")
        expl_layout = QVBoxLayout(expl_box)
        expl_layout.setContentsMargins(TDS.SPACE_MD, TDS.SPACE_SM, TDS.SPACE_MD, TDS.SPACE_SM)
        self.lbl_explanation = QLabel(
            "TEKIRA detectó múltiples interpretaciones viables.\n"
            "Selecciona la corrección adecuada."
        )
        self.lbl_explanation.setObjectName("ExplanationText")
        self.lbl_explanation.setWordWrap(True)
        expl_layout.addWidget(self.lbl_explanation)
        main_layout.addWidget(expl_box)

        main_layout.addSpacing(8)

        # Candidates
        candidates_label = QLabel("CANDIDATOS")
        candidates_label.setObjectName("SectionLabel")
        main_layout.addWidget(candidates_label)

        self.candidates_layout = QHBoxLayout()
        self.candidates_layout.setSpacing(TDS.SPACE_MD)
        main_layout.addLayout(self.candidates_layout)

        main_layout.addSpacing(12)

        # Manual Input
        manual_label = QLabel("CORRECCIÓN MANUAL")
        manual_label.setObjectName("SectionLabel")
        main_layout.addWidget(manual_label)

        manual_layout = QHBoxLayout()
        manual_layout.setSpacing(TDS.SPACE_SM)
        self.input_manual = QLineEdit()
        self.input_manual.setPlaceholderText("Escribe la corrección...")
        self.input_manual.setObjectName("TextInput")

        btn_apply = QPushButton("Aplicar")
        btn_apply.setObjectName("PrimaryBtn")
        btn_apply.clicked.connect(lambda: self.resolve_current(self.input_manual.text()))

        manual_layout.addWidget(self.input_manual)
        manual_layout.addWidget(btn_apply)
        main_layout.addLayout(manual_layout)

        layout.addWidget(self.main_area)

        # ── Bottom Controls ────────────────────────────
        controls = QHBoxLayout()
        btn_skip = QPushButton("Mantener original")
        btn_skip.setObjectName("SecondaryBtn")
        btn_skip.clicked.connect(self._skip_current)
        controls.addStretch()
        controls.addWidget(btn_skip)
        controls.addStretch()
        layout.addLayout(controls)

        # ── Completion State ───────────────────────────
        self.complete_area = QWidget()
        self.complete_area.hide()
        complete_layout = QVBoxLayout(self.complete_area)
        complete_layout.setAlignment(Qt.AlignCenter)

        done_label = QLabel("Revisión completada")
        done_label.setStyleSheet(
            f"font-size: {TDS.FONT_H1}px; font-weight: 700; color: {TDS.TEXT_PRIMARY};"
        )
        done_label.setAlignment(Qt.AlignCenter)

        done_sub = QLabel("Todas las ambigüedades han sido resueltas.")
        done_sub.setStyleSheet(
            f"font-size: {TDS.FONT_BODY}px; color: {TDS.TEXT_SECONDARY};"
        )
        done_sub.setAlignment(Qt.AlignCenter)

        btn_return = QPushButton("Volver al Dashboard")
        btn_return.setObjectName("PrimaryBtn")
        btn_return.clicked.connect(self.back_requested.emit)

        complete_layout.addStretch()
        complete_layout.addWidget(done_label)
        complete_layout.addSpacing(8)
        complete_layout.addWidget(done_sub)
        complete_layout.addSpacing(24)
        complete_layout.addWidget(btn_return, 0, Qt.AlignCenter)
        complete_layout.addStretch()
        layout.addWidget(self.complete_area)

    def load_job(self, job: DocumentJob):
        self.job = job
        if not job.result or not job.result.items:
            self.items = []
        else:
            self.items = [it for it in job.result.items if not it.is_resolved]
        self.current_idx = 0
        self.render_current()

    def render_current(self):
        if not self.items or self.current_idx >= len(self.items):
            self.main_area.hide()
            self.complete_area.show()
            self.lbl_progress.setText("Completado")
            return

        self.main_area.show()
        self.complete_area.hide()

        item = self.items[self.current_idx]
        self.lbl_progress.setText(f"{self.current_idx + 1} / {len(self.items)}")
        self.lbl_target.setText(item.original_word)

        # Highlight in context
        highlighted = item.context.replace(
            item.original_word,
            f'<span style="color: {TDS.TEXT_PRIMARY}; font-weight: 700;">'
            f'{item.original_word}</span>'
        )
        self.lbl_context.setText(f"…{highlighted}…")
        self.lbl_context.setTextFormat(Qt.RichText)

        # Clear candidates
        while self.candidates_layout.count():
            child = self.candidates_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for cand in item.candidates:
            w = cand["word"]
            btn = CandidateButton(w, cand["score"])
            btn.clicked.connect(lambda checked=False, w=w: self.resolve_current(w))
            self.candidates_layout.addWidget(btn)

        self.input_manual.clear()

        # Subtle fade-in for each card transition
        self._fade_effect = QGraphicsOpacityEffect(self.main_area)
        self.main_area.setGraphicsEffect(self._fade_effect)
        self._fade_anim = QPropertyAnimation(self._fade_effect, b"opacity")
        self._fade_anim.setDuration(TDS.ANIM_FAST)
        self._fade_anim.setStartValue(0.6)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_anim.start()

    def _skip_current(self):
        if self.items and self.current_idx < len(self.items):
            self.resolve_current(self.items[self.current_idx].original_word)

    def resolve_current(self, word: str):
        if not word.strip() or self.current_idx >= len(self.items):
            return
        item = self.items[self.current_idx]
        item.resolved_word = word
        item.is_resolved = True
        self.current_idx += 1
        self.render_current()
