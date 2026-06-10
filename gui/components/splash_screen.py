"""
Splash Screen — Esperanto Language Suite
Apple-inspired cinematic entry experience.
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
    """Full-window splash with staggered fade-in and dissolve-out."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SplashScreen")
        self.callback = None

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        # ── Brand Title ────────────────────────────────
        self.title = QLabel(TDS.BRAND_NAME)
        self.title.setObjectName("SplashTitle")
        self.title.setAlignment(Qt.AlignCenter)

        # ── Subtitle (powered by TEKIRA) ───────────────
        self.subtitle = QLabel(f'powered by <span style="color: {TDS.GOLD}; font-weight: 600;">TEKIRA</span>')
        self.subtitle.setObjectName("SplashSubtitle")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setTextFormat(Qt.RichText)

        # ── Progress Bar ───────────────────────────────
        self.progress = QProgressBar()
        self.progress.setObjectName("SplashProgress")
        self.progress.setFixedWidth(240)
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        layout.addStretch(3)
        layout.addWidget(self.title, 0, Qt.AlignCenter)
        layout.addSpacing(8)
        layout.addWidget(self.subtitle, 0, Qt.AlignCenter)
        layout.addSpacing(24)
        layout.addWidget(self.progress, 0, Qt.AlignCenter)
        layout.addStretch(4)

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
        """Begin the splash animation sequence."""
        self.callback = on_complete

        # Phase 1: Title fades in
        title_fade = QPropertyAnimation(self._title_effect, b"opacity")
        title_fade.setDuration(TDS.ANIM_SPLASH)
        title_fade.setStartValue(0)
        title_fade.setEndValue(1)
        title_fade.setEasingCurve(QEasingCurve.OutCubic)

        # Phase 2: Subtitle fades in
        sub_fade = QPropertyAnimation(self._sub_effect, b"opacity")
        sub_fade.setDuration(TDS.ANIM_NORMAL)
        sub_fade.setStartValue(0)
        sub_fade.setEndValue(1)
        sub_fade.setEasingCurve(QEasingCurve.OutCubic)

        # Phase 3: Progress bar appears
        prog_fade = QPropertyAnimation(self._prog_effect, b"opacity")
        prog_fade.setDuration(TDS.ANIM_FAST)
        prog_fade.setStartValue(0)
        prog_fade.setEndValue(1)
        prog_fade.setEasingCurve(QEasingCurve.OutCubic)

        self._entrance = QSequentialAnimationGroup()
        self._entrance.addAnimation(title_fade)
        self._entrance.addAnimation(sub_fade)
        self._entrance.addAnimation(prog_fade)
        self._entrance.finished.connect(self._start_progress)
        self._entrance.start()

    def _start_progress(self):
        """Animate the progress bar smoothly."""
        self._progress_anim = QPropertyAnimation(self.progress, b"value")
        self._progress_anim.setDuration(1200)
        self._progress_anim.setStartValue(0)
        self._progress_anim.setEndValue(100)
        self._progress_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._progress_anim.finished.connect(self._start_dissolve)
        self._progress_anim.start()

    def _start_dissolve(self):
        """Dissolve the entire splash — gentle upward drift + fade out."""
        self._self_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._self_effect)

        fade_out = QPropertyAnimation(self._self_effect, b"opacity")
        fade_out.setDuration(TDS.ANIM_SPLASH)
        fade_out.setStartValue(1)
        fade_out.setEndValue(0)
        fade_out.setEasingCurve(QEasingCurve.InOutCubic)

        drift_up = QPropertyAnimation(self, b"pos")
        drift_up.setDuration(TDS.ANIM_SPLASH)
        drift_up.setStartValue(self.pos())
        drift_up.setEndValue(QPoint(self.pos().x(), self.pos().y() - 30))
        drift_up.setEasingCurve(QEasingCurve.InCubic)

        self._dissolve = QParallelAnimationGroup()
        self._dissolve.addAnimation(fade_out)
        self._dissolve.addAnimation(drift_up)
        self._dissolve.finished.connect(self._on_done)
        self._dissolve.start()

    def _on_done(self):
        self.hide()
        if self.callback:
            self.callback()
