"""
Splash Screen — Esperanto Language Suite
Option 2 (Premium): Massive title, vertical subtitle, fluid cinematography.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QSequentialAnimationGroup, QParallelAnimationGroup, QPoint
)
from gui.styles.design_system import TDS


class SplashScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SplashScreen")
        self.callback = None

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # We use a massive container to center everything
        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setAlignment(Qt.AlignCenter)
        c_layout.setSpacing(0)

        # ── Brand Title ────────────────────────────────
        self.title = QLabel("Esperanto Language Suite")
        self.title.setObjectName("SplashTitle")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setWordWrap(True)

        c_layout.addWidget(self.title, 0, Qt.AlignCenter)
        c_layout.addSpacing(48)

        # ── Subtitle (Vertical Structure) ──────────────
        self.subtitle = QLabel(
            '<div style="text-align: center;">'
            f'<span style="font-size: 14px; font-weight: 400; color: #AEAEB2; letter-spacing: 2px;">powered by</span><br>'
            f'<span style="font-size: 28px; font-weight: 800; color: {TDS.GOLD}; letter-spacing: -0.5px;">TEKIRA</span>'
            '</div>'
        )
        self.subtitle.setObjectName("SplashSubtitle")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setTextFormat(Qt.RichText)

        c_layout.addWidget(self.subtitle, 0, Qt.AlignCenter)
        c_layout.addSpacing(64)

        # ── Progress Bar ───────────────────────────────
        self.progress = QProgressBar()
        self.progress.setObjectName("SplashProgress")
        self.progress.setFixedWidth(120)
        self.progress.setFixedHeight(2)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        c_layout.addWidget(self.progress, 0, Qt.AlignCenter)
        
        layout.addStretch()
        layout.addWidget(container)
        layout.addStretch()

        # ── Opacity effects ────────────────────────────
        self._title_effect = QGraphicsOpacityEffect(self.title)
        self._title_effect.setOpacity(0)
        self.title.setGraphicsEffect(self._title_effect)

        self._sub_effect = QGraphicsOpacityEffect(self.subtitle)
        self._sub_effect.setOpacity(0)
        self.subtitle.setGraphicsEffect(self._sub_effect)

        self._prog_effect = QGraphicsOpacityEffect(self.progress)
        self._prog_effect.setOpacity(0)
        self.progress.setGraphicsEffect(self._prog_effect)

    def start(self, on_complete):
        """Begin Option 2 (Premium) sequence (3.4s total)."""
        self.callback = on_complete

        # 0 - 400ms: Title Fade In
        title_fade = QPropertyAnimation(self._title_effect, b"opacity")
        title_fade.setDuration(400)
        title_fade.setStartValue(0)
        title_fade.setEndValue(1)
        title_fade.setEasingCurve(QEasingCurve.OutCubic)

        # 600 - 1000ms: Subtitle + Progress Fade In
        sub_fade = QPropertyAnimation(self._sub_effect, b"opacity")
        sub_fade.setDuration(400)
        sub_fade.setStartValue(0)
        sub_fade.setEndValue(1)
        sub_fade.setEasingCurve(QEasingCurve.OutCubic)

        prog_fade = QPropertyAnimation(self._prog_effect, b"opacity")
        prog_fade.setDuration(400)
        prog_fade.setStartValue(0)
        prog_fade.setEndValue(1)
        prog_fade.setEasingCurve(QEasingCurve.OutCubic)

        self._parallel_sub_prog = QParallelAnimationGroup()
        self._parallel_sub_prog.addAnimation(sub_fade)
        self._parallel_sub_prog.addAnimation(prog_fade)

        # Sequence Builder
        self._entrance = QSequentialAnimationGroup()
        self._entrance.addAnimation(title_fade)
        self._entrance.addPause(200) # Anchor the title
        self._entrance.addAnimation(self._parallel_sub_prog)
        self._entrance.addPause(100) # Tiny breath before progress
        
        self._entrance.finished.connect(self._start_progress)
        self._entrance.start()

    def _start_progress(self):
        """1100 - 2600ms: Progress fluid animation"""
        self._progress_anim = QPropertyAnimation(self.progress, b"value")
        self._progress_anim.setDuration(1500)
        self._progress_anim.setStartValue(0)
        self._progress_anim.setEndValue(100)
        self._progress_anim.setEasingCurve(QEasingCurve.InOutCubic)
        
        self._prog_group = QSequentialAnimationGroup()
        self._prog_group.addAnimation(self._progress_anim)
        self._prog_group.addPause(300) # Confirmation pause
        self._prog_group.finished.connect(self._start_dissolve)
        self._prog_group.start()

    def _start_dissolve(self):
        """2900 - 3400ms: Dissolve (Drift & Fade Out)"""
        self._self_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._self_effect)

        fade_out = QPropertyAnimation(self._self_effect, b"opacity")
        fade_out.setDuration(500)
        fade_out.setStartValue(1)
        fade_out.setEndValue(0)
        fade_out.setEasingCurve(QEasingCurve.InOutSine)

        drift_up = QPropertyAnimation(self, b"pos")
        drift_up.setDuration(500)
        drift_up.setStartValue(self.pos())
        drift_up.setEndValue(QPoint(self.pos().x(), self.pos().y() - 20))
        drift_up.setEasingCurve(QEasingCurve.OutCubic)

        self._dissolve = QParallelAnimationGroup()
        self._dissolve.addAnimation(fade_out)
        self._dissolve.addAnimation(drift_up)
        self._dissolve.finished.connect(self._on_done)
        self._dissolve.start()

    def _on_done(self):
        self.hide()
        if self.callback:
            self.callback()
