"""
Genesis Overlay — Constancia Estructural
This replaces the traditional Splash Screen. It overlays the main UI,
displays the welcome title, and morphs its geometry to seamlessly become
the Sidebar brand logo.
"""
from PySide6.QtWidgets import (
    QWidget, QLabel, QGraphicsOpacityEffect, QVBoxLayout
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup,
    QParallelAnimationGroup, QPoint, QVariantAnimation
)
from PySide6.QtGui import QFont, QColor
from gui.styles.design_system import TDS


class GenesisOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GenesisOverlay")
        self.setStyleSheet("background-color: transparent;")
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        self.callback = None
        self.target_widget = None
        
        # Central layout to prevent positioning jitter during window resizing
        self.overlay_layout = QVBoxLayout(self)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)
        self.overlay_layout.setSpacing(60) # Spacing between title and subtitle
        self.overlay_layout.setAlignment(Qt.AlignCenter)

        # Floating labels (managed by layout to prevent jitter)
        self.lbl_title = QLabel("Esperanto Language Suite", self)
        self.lbl_title.setStyleSheet(
            f"font-family: {TDS.FONT_FAMILY_SERIF}; "
            f"font-size: 96px; "
            f"font-weight: 800; "
            f"color: #111111; "
            f"letter-spacing: -3px;"
        )
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.overlay_layout.addWidget(self.lbl_title)

        self.lbl_subtitle = QLabel(self)
        self.lbl_subtitle.setText(
            '<div style="text-align: center;">'
            f'<span style="font-size: 11px; font-weight: 400; color: #AEAEB2; letter-spacing: 4px;">POWERED BY</span><br>'
            f'<span style="font-size: 28px; font-weight: 800; color: {TDS.GOLD}; letter-spacing: -0.5px;">TEKIRA</span>'
            '</div>'
        )
        self.lbl_subtitle.setAlignment(Qt.AlignCenter)
        self.overlay_layout.addWidget(self.lbl_subtitle)

        # Opacity effects
        self._title_effect = QGraphicsOpacityEffect(self.lbl_title)
        self._title_effect.setOpacity(0)
        self.lbl_title.setGraphicsEffect(self._title_effect)

        self._sub_effect = QGraphicsOpacityEffect(self.lbl_subtitle)
        self._sub_effect.setOpacity(0)
        self.lbl_subtitle.setGraphicsEffect(self._sub_effect)

        self._bg_effect = QGraphicsOpacityEffect(self)
        self._bg_effect.setOpacity(1)
        self.setGraphicsEffect(self._bg_effect)

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def start(self, main_container, on_complete):
        """
        main_container: The actual app UI we need to fade in underneath.
        """
        self.callback = on_complete
        
        # Ensure main UI is invisible but layout is calculated
        from PySide6.QtWidgets import QGraphicsBlurEffect
        self._main_effect = QGraphicsOpacityEffect(main_container)
        self._main_effect.setOpacity(0)
        main_container.setGraphicsEffect(self._main_effect)

        # 1. Fade In Welcome (The Awakening)
        t_fade_in = QPropertyAnimation(self._title_effect, b"opacity")
        t_fade_in.setDuration(600)
        t_fade_in.setStartValue(0)
        t_fade_in.setEndValue(1)
        t_fade_in.setEasingCurve(QEasingCurve.OutCubic)

        s_fade_in = QPropertyAnimation(self._sub_effect, b"opacity")
        s_fade_in.setDuration(500)
        s_fade_in.setStartValue(0)
        s_fade_in.setEndValue(1)
        s_fade_in.setEasingCurve(QEasingCurve.OutCubic)

        # Sequence
        seq = QSequentialAnimationGroup(self)
        seq.addAnimation(t_fade_in)
        seq.addPause(600)
        seq.addAnimation(s_fade_in)
        seq.addPause(800) # Deep absorption pause for the Aura to shine
        seq.finished.connect(lambda: self._execute_bloom(main_container))
        seq.start()

    def _execute_bloom(self, main_container):
        from PySide6.QtWidgets import QGraphicsBlurEffect
        
        # Add blur effect to the overlay text to simulate blooming away
        self._blur_effect = QGraphicsBlurEffect(self)
        self._blur_effect.setBlurRadius(0)
        # We need to preserve opacity effect on the background, 
        # but QWidget only takes one graphics effect.
        # Instead, we apply blur to the title and subtitle labels directly.
        self._title_blur = QGraphicsBlurEffect(self.lbl_title)
        self._title_blur.setBlurRadius(0)
        self.lbl_title.setGraphicsEffect(self._title_blur)
        
        self._sub_blur = QGraphicsBlurEffect(self.lbl_subtitle)
        self._sub_blur.setBlurRadius(0)
        self.lbl_subtitle.setGraphicsEffect(self._sub_blur)

        # Animate blur
        blur_title_anim = QPropertyAnimation(self._title_blur, b"blurRadius")
        blur_title_anim.setDuration(1200)
        blur_title_anim.setStartValue(0)
        blur_title_anim.setEndValue(30)
        blur_title_anim.setEasingCurve(QEasingCurve.InOutSine)

        blur_sub_anim = QPropertyAnimation(self._sub_blur, b"blurRadius")
        blur_sub_anim.setDuration(1200)
        blur_sub_anim.setStartValue(0)
        blur_sub_anim.setEndValue(30)
        blur_sub_anim.setEasingCurve(QEasingCurve.InOutSine)

        # Transmute the Overlay (Fade Out)
        overlay_fade = QPropertyAnimation(self._bg_effect, b"opacity")
        overlay_fade.setDuration(1200)
        overlay_fade.setStartValue(1)
        overlay_fade.setEndValue(0)
        overlay_fade.setEasingCurve(QEasingCurve.InOutSine)

        # Fade in main container slowly
        main_fade = QPropertyAnimation(self._main_effect, b"opacity")
        main_fade.setDuration(1200)
        main_fade.setStartValue(0)
        main_fade.setEndValue(1)
        main_fade.setEasingCurve(QEasingCurve.InOutSine)

        # Parallel Bloom
        self.morph_group = QParallelAnimationGroup(self)
        self.morph_group.addAnimation(blur_title_anim)
        self.morph_group.addAnimation(blur_sub_anim)
        self.morph_group.addAnimation(overlay_fade)
        self.morph_group.addAnimation(main_fade)

        self.morph_group.finished.connect(self._on_done)
        self.morph_group.start()

    def _on_done(self):
        self.hide()
        if self.callback:
            self.callback()
