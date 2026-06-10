"""
Tekira Aura — Atmosfera Espacial
Un widget que renderiza un inmenso gradiente radial dorado, 
animado sutilmente para simular una "respiración" o latido de fondo.
"""
import math
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QRadialGradient, QColor
from PySide6.QtCore import QTimer, Qt
from gui.styles.design_system import TDS


class TekiraAura(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TekiraAura")
        # Ensure it sits at the absolute back and ignores mouse events
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: transparent;")
        
        self.phase = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_aura)
        self.timer.start(50)  # ~20 FPS for ambient background is enough

        self.center_x_offset = 0.5
        self.center_y_offset = 0.5
        self.intensity = 0.0

    def set_target_state(self, state: str):
        """Transitions aura behavior based on app state."""
        pass  # Future proofing for 'idle', 'processing', 'alert'

    def _animate_aura(self):
        # Extremely slow sine wave breathing
        self.phase += 0.02
        # Slight drift in X and Y
        self.center_x_offset = 0.5 + math.sin(self.phase * 0.5) * 0.05
        self.center_y_offset = 0.5 + math.cos(self.phase * 0.3) * 0.05
        
        # Intensity pulse
        self.intensity = (math.sin(self.phase * 0.8) + 1.0) / 2.0  # 0.0 to 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter()
        if not painter.begin(self):
            return
            
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx = w * self.center_x_offset
        cy = h * self.center_y_offset
        
        # Massive radius so it acts as an ambient glow
        radius = max(w, h) * 0.8

        gradient = QRadialGradient(cx, cy, radius)
        
        # Base color is pure white, gold is the aura
        # Max opacity is 60-80% at center, around 20-30% at mid
        base_alpha = 60 + int(20 * self.intensity)
        mid_alpha = 20 + int(10 * self.intensity)
        gold = QColor(TDS.GOLD)
        
        center_color = QColor(gold.red(), gold.green(), gold.blue(), base_alpha)
        mid_color = QColor(gold.red(), gold.green(), gold.blue(), mid_alpha)
        edge_color = QColor(gold.red(), gold.green(), gold.blue(), 0)

        gradient.setColorAt(0.0, center_color)
        gradient.setColorAt(0.5, mid_color)
        gradient.setColorAt(1.0, edge_color)

        painter.fillRect(self.rect(), gradient)
        painter.end()
