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
        # Solid background matching the app's base
        self.setStyleSheet(f"background-color: {TDS.BG_SECONDARY};")
        
        self.callback = None
        self.target_widget = None

        # Floating labels (absolute positioned later)
        self.lbl_title = QLabel("Esperanto Language Suite", self)
        self.lbl_title.setStyleSheet(f"font-size: 80px; font-weight: 800; color: #111111; letter-spacing: -2px;")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.adjustSize()

        self.lbl_subtitle = QLabel(self)
        self.lbl_subtitle.setText(
            '<div style="text-align: center;">'
            f'<span style="font-size: 14px; font-weight: 400; color: #AEAEB2; letter-spacing: 2px;">powered by</span><br>'
            f'<span style="font-size: 28px; font-weight: 800; color: {TDS.GOLD}; letter-spacing: -0.5px;">TEKIRA</span>'
            '</div>'
        )
        self.lbl_subtitle.setAlignment(Qt.AlignCenter)
        self.lbl_subtitle.adjustSize()

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
        # Center elements initially
        w, h = self.width(), self.height()
        
        tw, th = self.lbl_title.width(), self.lbl_title.height()
        self.lbl_title.move((w - tw) // 2, (h - th) // 2 - 40)
        
        sw, sh = self.lbl_subtitle.width(), self.lbl_subtitle.height()
        self.lbl_subtitle.move((w - sw) // 2, (h - sh) // 2 + 60)

    def start(self, target_widget, main_container, on_complete):
        """
        target_widget: The SidebarBrand QLabel we will morph into.
        main_container: The actual app UI we need to fade in underneath.
        """
        self.target_widget = target_widget
        self.callback = on_complete
        
        # Ensure main UI is invisible but layout is calculated
        self._main_effect = QGraphicsOpacityEffect(main_container)
        self._main_effect.setOpacity(0)
        main_container.setGraphicsEffect(self._main_effect)

        # 1. Fade In Welcome
        t_fade_in = QPropertyAnimation(self._title_effect, b"opacity")
        t_fade_in.setDuration(400)
        t_fade_in.setStartValue(0)
        t_fade_in.setEndValue(1)
        t_fade_in.setEasingCurve(QEasingCurve.OutCubic)

        s_fade_in = QPropertyAnimation(self._sub_effect, b"opacity")
        s_fade_in.setDuration(400)
        s_fade_in.setStartValue(0)
        s_fade_in.setEndValue(1)
        s_fade_in.setEasingCurve(QEasingCurve.OutCubic)

        # 2. Fade Out TEKIRA (to leave title alone)
        s_fade_out = QPropertyAnimation(self._sub_effect, b"opacity")
        s_fade_out.setDuration(300)
        s_fade_out.setStartValue(1)
        s_fade_out.setEndValue(0)
        s_fade_out.setEasingCurve(QEasingCurve.InCubic)

        # Sequence
        seq = QSequentialAnimationGroup(self)
        seq.addAnimation(t_fade_in)
        seq.addPause(200)
        seq.addAnimation(s_fade_in)
        seq.addPause(800) # Deep absorption pause
        seq.addAnimation(s_fade_out)
        seq.finished.connect(lambda: self._execute_morph(main_container))
        seq.start()

    def _execute_morph(self, main_container):
        # Calculate target global geometry
        target_pos = self.target_widget.mapToGlobal(QPoint(0, 0))
        # Map back to overlay coords
        local_target_pos = self.mapFromGlobal(target_pos)
        
        # We need to morph the text content and size simultaneously
        font_anim = QVariantAnimation(self)
        font_anim.setDuration(800)
        font_anim.setStartValue(80.0)
        font_anim.setEndValue(13.0) # Matches FONT_CAPTION
        font_anim.setEasingCurve(QEasingCurve.InOutCubic)
        
        def update_font(val):
            # As the font shrinks, we crossfade the text conceptually
            # At 50% way, swap text
            if val < 40 and self.lbl_title.text() != "ESPERANTO":
                self.lbl_title.setText("ESPERANTO")
                self.lbl_title.adjustSize()
                
            self.lbl_title.setStyleSheet(
                f"font-size: {int(val)}px; font-weight: {'800' if val > 40 else '600'}; "
                f"color: {'#111111' if val > 40 else TDS.TEXT_SECONDARY}; "
                f"letter-spacing: {'-2px' if val > 40 else '0.5px'};"
            )
            # Re-adjust size to prevent clipping during animation
            self.lbl_title.adjustSize()
            
        font_anim.valueChanged.connect(update_font)

        # Pos animation
        pos_anim = QPropertyAnimation(self.lbl_title, b"pos")
        pos_anim.setDuration(800)
        pos_anim.setStartValue(self.lbl_title.pos())
        # Add slight offset to match padding
        pos_anim.setEndValue(local_target_pos)
        pos_anim.setEasingCurve(QEasingCurve.InOutCubic)

        # Fade out the overlay background to reveal main_container
        bg_fade = QPropertyAnimation(self._bg_effect, b"opacity")
        bg_fade.setDuration(800)
        bg_fade.setStartValue(1)
        bg_fade.setEndValue(0)
        bg_fade.setEasingCurve(QEasingCurve.InOutCubic)

        # Fade in main container
        main_fade = QPropertyAnimation(self._main_effect, b"opacity")
        main_fade.setDuration(800)
        main_fade.setStartValue(0)
        main_fade.setEndValue(1)
        main_fade.setEasingCurve(QEasingCurve.InOutCubic)

        # Parallel transmutations
        self.morph_group = QParallelAnimationGroup(self)
        self.morph_group.addAnimation(font_anim)
        self.morph_group.addAnimation(pos_anim)
        self.morph_group.addAnimation(bg_fade)
        self.morph_group.addAnimation(main_fade)

        self.morph_group.finished.connect(self._on_done)
        self.morph_group.start()

    def _on_done(self):
        self.hide()
        # Show actual brand label
        self.target_widget.setGraphicsEffect(None)
        if self.callback:
            self.callback()
