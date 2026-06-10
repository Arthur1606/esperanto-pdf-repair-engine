"""
Physical Canvas Lab — Standalone proof of concept.
Validates composition, atmosphere, materials, lighting, and multi-layer shadows.
"""
import sys
import math
import random
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property, QRectF
from PySide6.QtGui import QPainter, QRadialGradient, QLinearGradient, QColor, QBrush, QImage, QPixmap, QPen, QFont

# Cotton paper texture generator (with random fibers)
def generate_cotton_pixmap(w=128, h=128, is_card=False, finish="light"):
    image = QImage(w, h, QImage.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))
    
    # Base organic pulp grain
    for y in range(h):
        for x in range(w):
            g1 = random.randint(120, 160)
            if finish in ["sidebar_bg", "full"] and not is_card: # background pulp clumping
                pulp = math.sin(x * 0.08) * math.cos(y * 0.08) * 12
                g = int(max(0, min(255, g1 + pulp)))
            elif finish == "full" and is_card: # card pulp clumping
                pulp = math.sin(x * 0.08) * math.cos(y * 0.08) * 15
                g = int(max(0, min(255, g1 + pulp)))
            else:
                g = g1
            
            alpha = 10 if (is_card and finish == "full") else 6
            image.setPixelColor(x, y, QColor(g, g, g, alpha))
            
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    
    if finish == "full" and is_card:
        # Curved organic fibers (Premium)
        for _ in range(120):
            x1 = random.randint(0, w)
            y1 = random.randint(0, h)
            length = random.randint(3, 10)
            angle = random.uniform(0, 2 * math.pi)
            x2 = x1 + int(length * math.cos(angle))
            y2 = y1 + int(length * math.sin(angle))
            color_choice = random.choice([
                QColor(139, 115, 85, random.randint(10, 25)),
                QColor(180, 180, 180, random.randint(12, 28)),
            ])
            painter.setPen(QPen(color_choice, random.uniform(0.7, 1.2)))
            if random.random() > 0.5:
                from PySide6.QtGui import QPainterPath
                path = QPainterPath()
                path.moveTo(x1, y1)
                cx = (x1 + x2) / 2 + random.randint(-2, 2)
                cy = (y1 + y2) / 2 + random.randint(-2, 2)
                path.quadTo(cx, cy, x2, y2)
                painter.drawPath(path)
            else:
                painter.drawLine(x1, y1, x2, y2)
                
        # Reflective fibers
        painter.setPen(QPen(QColor(255, 255, 255, 35), 0.8))
        for _ in range(60):
            x1 = random.randint(0, w)
            y1 = random.randint(0, h)
            length = random.randint(4, 12)
            angle = random.uniform(0, 2 * math.pi)
            x2 = x1 + int(length * math.cos(angle))
            y2 = y1 + int(length * math.sin(angle))
            painter.drawLine(x1, y1, x2, y2)
    else:
        # Standard straight fibers (V14-Light)
        painter.setPen(QPen(QColor(180, 180, 180, 16), 1.0))
        for _ in range(70):
            x1 = random.randint(0, w)
            y1 = random.randint(0, h)
            x2 = x1 + random.randint(-6, 6)
            y2 = y1 + random.randint(-6, 6)
            painter.drawLine(x1, y1, x2, y2)
            
    painter.end()
    return QPixmap.fromImage(image)

# Anodized brushed metal texture generator
def generate_metal_pixmap(w=128, h=128, finish="light"):
    image = QImage(w, h, QImage.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    
    if finish in ["sidebar_bg", "full"]:
        # Advanced metal brushed texture (double polarity)
        for _ in range(400):
            x = random.randint(0, w)
            y1 = random.randint(0, h)
            length = random.randint(20, 80)
            opacity = random.randint(3, 10)
            thickness = random.choice([1.0, 1.5])
            painter.setPen(QPen(QColor(255, 255, 255, opacity), thickness))
            painter.drawLine(x, y1, x, y1 + length)
            
        for _ in range(300):
            x = random.randint(0, w)
            y1 = random.randint(0, h)
            length = random.randint(15, 60)
            opacity = random.randint(4, 12)
            painter.setPen(QPen(QColor(0, 0, 0, opacity), 1.0))
            painter.drawLine(x, y1, x, y1 + length)
    else:
        # Standard brushed metal
        painter.setPen(QPen(QColor(255, 255, 255, 6), 1.0))
        for _ in range(130):
            x = random.randint(0, w)
            y1 = random.randint(0, h)
            length = random.randint(15, 45)
            painter.drawLine(x, y1, x, y1 + length)
            
    painter.end()
    return QPixmap.fromImage(image)

class LivingBackground(QWidget):
    def __init__(self, parent=None, finish="light"):
        super().__init__(parent)
        self.finish = finish
        self.phase = 0.0
        # Tiled noise for warm background
        self.noise_px = generate_cotton_pixmap(128, 128, is_card=False, finish=finish)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(33) # ~30 FPS
        
    def tick(self):
        self.phase += 0.015
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # 1. Base warmth fill (#F5F4F0 - Warm Editorial Off-white)
        painter.fillRect(self.rect(), QColor(245, 244, 240))
        
        if self.finish in ["sidebar_bg", "full"]:
            # 2. Pulsing Aura of TEKIRA (Three overlapping radial lights)
            # Light 1: Golden Core
            cx1 = w * (0.4 + math.sin(self.phase * 0.7) * 0.08)
            cy1 = h * (0.6 + math.cos(self.phase * 0.5) * 0.08)
            r1 = max(w, h) * 0.75
            g1 = QRadialGradient(cx1, cy1, r1)
            g1.setColorAt(0.0, QColor(201, 162, 39, 42))  # Gold aura core
            g1.setColorAt(0.4, QColor(201, 162, 39, 16))
            g1.setColorAt(1.0, QColor(201, 162, 39, 0))
            painter.fillRect(self.rect(), g1)
            
            # Light 2: Amber Bleed
            cx2 = w * (0.55 + math.cos(self.phase * 0.6) * 0.06)
            cy2 = h * (0.45 + math.sin(self.phase * 0.8) * 0.06)
            r2 = max(w, h) * 0.5
            g2 = QRadialGradient(cx2, cy2, r2)
            g2.setColorAt(0.0, QColor(230, 120, 40, 18))  # Amber warmth
            g2.setColorAt(0.6, QColor(230, 120, 40, 4))
            g2.setColorAt(1.0, QColor(230, 120, 40, 0))
            painter.fillRect(self.rect(), g2)
            
            # Light 3: Champagne Soft Shine
            cx3 = w * (0.3 + math.sin(self.phase * 1.1) * 0.04)
            cy3 = h * (0.3 + math.cos(self.phase * 0.9) * 0.04)
            r3 = max(w, h) * 0.4
            g3 = QRadialGradient(cx3, cy3, r3)
            g3.setColorAt(0.0, QColor(255, 230, 180, 25))  # Champagne highlight
            g3.setColorAt(0.5, QColor(255, 230, 180, 5))
            g3.setColorAt(1.0, QColor(255, 230, 180, 0))
            painter.fillRect(self.rect(), g3)
        else:
            # V14-Light background: 2 radial lights, no vignette, no sidebar shadow
            cx1 = w * (0.4 + math.sin(self.phase * 0.7) * 0.08)
            cy1 = h * (0.6 + math.cos(self.phase * 0.5) * 0.08)
            r1 = max(w, h) * 0.75
            g1 = QRadialGradient(cx1, cy1, r1)
            g1.setColorAt(0.0, QColor(201, 162, 39, 45))
            g1.setColorAt(0.4, QColor(201, 162, 39, 18))
            g1.setColorAt(1.0, QColor(201, 162, 39, 0))
            painter.fillRect(self.rect(), g1)
            
            cx2 = w * (0.55 + math.cos(self.phase * 0.6) * 0.06)
            cy2 = h * (0.45 + math.sin(self.phase * 0.8) * 0.06)
            r2 = max(w, h) * 0.5
            g2 = QRadialGradient(cx2, cy2, r2)
            g2.setColorAt(0.0, QColor(230, 120, 40, 20))
            g2.setColorAt(0.6, QColor(230, 120, 40, 5))
            g2.setColorAt(1.0, QColor(230, 120, 40, 0))
            painter.fillRect(self.rect(), g2)
            
        # 3. Micro-grain Noise overlay
        painter.setOpacity(1.0)
        painter.drawTiledPixmap(self.rect(), self.noise_px)
        
        # 4. Vignette / Edge Ambient Occlusion (only in sidebar_bg / full)
        if self.finish in ["sidebar_bg", "full"]:
            vignette = QRadialGradient(w / 2, h / 2, max(w, h) * 0.65)
            vignette.setColorAt(0.0, QColor(0, 0, 0, 0))
            vignette.setColorAt(0.7, QColor(30, 25, 20, 6))
            vignette.setColorAt(1.0, QColor(20, 15, 10, 22))
            painter.fillRect(self.rect(), vignette)
            
            # 5. Shadow from Sidebar to Central Canvas (Separation of Planos)
            sidebar_shadow = QLinearGradient(240, 0, 265, 0)
            sidebar_shadow.setColorAt(0.0, QColor(0, 0, 0, 75))
            sidebar_shadow.setColorAt(0.15, QColor(0, 0, 0, 40))
            sidebar_shadow.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.fillRect(240, 0, 25, h, sidebar_shadow)

class TexturedSidebar(QWidget):
    def __init__(self, parent=None, draw_text=True, finish="light"):
        super().__init__(parent)
        self.finish = finish
        self.setFixedWidth(240)
        self.draw_text = draw_text
        self.noise_px = generate_metal_pixmap(128, 128, finish=finish)
        self.setAttribute(Qt.WA_StyledBackground, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Sidebar Deep Charcoal/Graphite base (#0C0C0D)
        painter.fillRect(self.rect(), QColor(12, 12, 13))
        
        # 2. Tiled Brushed Metal Noise
        painter.drawTiledPixmap(self.rect(), self.noise_px)
        
        # 3. Soft internal gradient and Anisotropic Glare
        if self.finish in ["sidebar_bg", "full"]:
            # Specular anisotropic vertical highlight band in the middle
            grad = QLinearGradient(0, 0, self.width(), 0)
            grad.setColorAt(0.0, QColor(255, 255, 255, 12))
            grad.setColorAt(0.2, QColor(255, 255, 255, 4))
            grad.setColorAt(0.45, QColor(255, 255, 255, 18))  # Metallic anisotropic sheen peak
            grad.setColorAt(0.55, QColor(255, 255, 255, 8))
            grad.setColorAt(0.8, QColor(0, 0, 0, 10))
            grad.setColorAt(1.0, QColor(0, 0, 0, 35))
            painter.fillRect(self.rect(), grad)
            
            # Subtle top-down shading
            v_grad = QLinearGradient(0, 0, 0, self.height())
            v_grad.setColorAt(0.0, QColor(255, 255, 255, 15))
            v_grad.setColorAt(0.5, QColor(0, 0, 0, 0))
            v_grad.setColorAt(1.0, QColor(0, 0, 0, 50))
            painter.fillRect(self.rect(), v_grad)
            
            # 4. Right Bevel Border (1px micro-bevel reflection + 1px dark groove shadow)
            painter.setPen(QColor(255, 255, 255, 18))
            painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())
            painter.setPen(QColor(0, 0, 0, 80))
            painter.drawLine(self.width() - 2, 0, self.width() - 2, self.height())
        else:
            # V14-Light simple sidebar gradient
            grad = QLinearGradient(0, 0, self.width(), self.height())
            grad.setColorAt(0.0, QColor(255, 255, 255, 8))
            grad.setColorAt(0.4, QColor(0, 0, 0, 0))
            grad.setColorAt(1.0, QColor(0, 0, 0, 45))
            painter.fillRect(self.rect(), grad)
            
            # Simple right white reflection line
            painter.setPen(QColor(255, 255, 255, 12))
            painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())
        
        if self.draw_text:
            painter.setPen(QColor(255, 255, 255, 200))
            font = painter.font()
            font.setFamily("Georgia")
            font.setPixelSize(18)
            font.setLetterSpacing(QFont.AbsoluteSpacing, 3)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(24, 60, "ESPERANTO")
        else:
            # Mode D: Pure composition mass (blank placeholder block for logo)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255, 25))
            painter.drawRoundedRect(24, 45, 100, 14, 3, 3)
            
            # Nav items representation as grey blocks
            for i in range(4):
                painter.drawRoundedRect(24, 110 + (i * 38), 120, 12, 3, 3)
                
            # Profile widget mass at the bottom
            py = self.height() - 70
            painter.drawRoundedRect(24, py, 192, 46, 6, 6)

class BaseCottonCard(QWidget):
    def __init__(self, width, height, parent=None, dashed=False, has_progress=False, progress_val=0.0, draw_text=False, finish="light"):
        super().__init__(parent)
        self.finish = finish
        self.setFixedSize(width, height)
        self.dashed = dashed
        self.has_progress = has_progress
        self.progress_val = progress_val
        self.draw_text = draw_text
        
        self.noise_px = generate_cotton_pixmap(128, 128, is_card=True, finish=finish)
        self._hover_val = 0.0
        
        self.anim = QPropertyAnimation(self, b"hover_val")
        self.anim.setDuration(220)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

    def get_hover_val(self):
        return self._hover_val

    def set_hover_val(self, val):
        self._hover_val = val
        self.update()

    hover_val = Property(float, get_hover_val, set_hover_val)

    def enterEvent(self, event):
        super().enterEvent(event)
        self.anim.stop()
        self.anim.setStartValue(self._hover_val)
        self.anim.setEndValue(1.0)
        self.anim.start()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.anim.stop()
        self.anim.setStartValue(self._hover_val)
        self.anim.setEndValue(0.0)
        self.anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Geometry margins for shadow bleed
        margin = 30
        card_w = w - (margin * 2)
        card_h = h - (margin * 2)
        
        lift = self._hover_val * 8.0
        rx = margin
        ry = margin - lift
        card_rect = QRectF(rx, ry, card_w, card_h)
        
        # ── 1. Concentric Soft Rectangular Shadows (Ambient Occlusion) ──
        # Layer A: Sombra de Oclusión Corta (Contact Shadow)
        # Fine and dark close to the base, fading as card lifts
        contact_alpha = 45 - int(self._hover_val * 30)
        contact_offset = 1.0 + (self._hover_val * 1.0)
        contact_layers = 6
        for i in range(contact_layers):
            expand = (i / contact_layers) * 4.0
            s_rect = card_rect.adjusted(-expand, -expand, expand, expand)
            s_rect.translate(0, contact_offset * (i / contact_layers))
            alpha = int(contact_alpha * ((1.0 - i / contact_layers) ** 2.0))
            if alpha > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(15, 12, 10, alpha))
                painter.drawRoundedRect(s_rect, 12 + expand, 12 + expand)

        # Layer B: Sombra Media Proyectada (Cast Shadow)
        # Soft and expanding based on the elevation (hover)
        cast_alpha = 22 - int(self._hover_val * 8)
        cast_offset = 3.0 + (self._hover_val * 9.0)  # y-offset 3px -> 12px
        cast_layers = 12
        for i in range(cast_layers):
            expand = (i / cast_layers) * (8.0 + self._hover_val * 16.0) # spread 8px -> 24px
            s_rect = card_rect.adjusted(-expand, -expand, expand, expand)
            s_rect.translate(0, cast_offset * (i / cast_layers))
            alpha = int(cast_alpha * ((1.0 - i / cast_layers) ** 2.0))
            if alpha > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(30, 26, 20, alpha))
                painter.drawRoundedRect(s_rect, 12 + expand, 12 + expand)

        # Layer C: Halo de Luz Ambiente (Ambient Glow)
        # Wide, diffuse gold/amber shadow emulating TEKIRA's ambient glow
        glow_alpha = 12 - int(self._hover_val * 4)
        glow_offset = 6.0 + (self._hover_val * 12.0)  # y-offset 6px -> 18px
        glow_layers = 20
        for i in range(glow_layers):
            expand = (i / glow_layers) * (20.0 + self._hover_val * 30.0) # spread 20px -> 50px
            s_rect = card_rect.adjusted(-expand, -expand, expand, expand)
            s_rect.translate(0, glow_offset * (i / glow_layers))
            alpha = int(glow_alpha * ((1.0 - i / glow_layers) ** 3.0))
            if alpha > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(180, 140, 60, alpha))
                painter.drawRoundedRect(s_rect, 12 + expand, 12 + expand)

        # ── 2. Bisel 3D y Volumen Coherente (Plaqueta de Papel) ──
        # Grosor de Plaqueta: Draw a bottom edge to give it a 3D plate thickness
        # Uses a slightly darker paper/grey tone
        plate_rect = card_rect.translated(0, 1.0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(218, 216, 210))
        painter.drawRoundedRect(plate_rect, 12, 12)

        # ── 3. Draw Cotton Paper Body (#FAFAF9) ──
        painter.setBrush(QBrush(QColor(250, 249, 246)))
        painter.drawRoundedRect(card_rect, 12, 12)
        
        # ── 4. Paper Texture constrained ──
        painter.save()
        from PySide6.QtGui import QPainterPath
        clip_path = QPainterPath()
        clip_path.addRoundedRect(card_rect, 12, 12)
        painter.setClipPath(clip_path)
        painter.drawTiledPixmap(card_rect.toRect(), self.noise_px)
        
        # Sheen glaze
        grad_sheen = QLinearGradient(card_rect.topLeft(), card_rect.bottomLeft())
        grad_sheen.setColorAt(0.0, QColor(255, 255, 255, 20))
        grad_sheen.setColorAt(1.0, QColor(0, 0, 0, 6))
        painter.fillRect(card_rect, grad_sheen)
        
        # ── 5. Inner Micro-Bevel Border with Directed Lighting ──
        # Directed light: top-left highlight (Bisel Superior) and bottom-right shadow (Borde Inferior)
        grad_border = QLinearGradient(card_rect.topLeft(), card_rect.bottomRight())
        grad_border.setColorAt(0.0, QColor(255, 255, 255, 230))  # Bisel Superior
        grad_border.setColorAt(0.35, QColor(255, 255, 255, 80))
        grad_border.setColorAt(0.5, QColor(0, 0, 0, 0))
        grad_border.setColorAt(0.65, QColor(0, 0, 0, 15))
        grad_border.setColorAt(1.0, QColor(0, 0, 0, 50))        # Borde de Sombra Inferior
        
        border_pen = QPen(QBrush(grad_border), 1.2)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(clip_path)
        
        # ── 6. Features ──
        if self.dashed:
            if self.finish == "full":
                # Blind stitching (physical debossed costura)
                # Highlight
                painter.setPen(QPen(QColor(255, 255, 255, 180), 1.5, Qt.DashLine))
                painter.drawRoundedRect(card_rect.adjusted(6, 6.8, -6, -5.2), 8, 8)
                # Shadow
                painter.setPen(QPen(QColor(15, 10, 5, 40), 1.5, Qt.DashLine))
                painter.drawRoundedRect(card_rect.adjusted(6, 5.2, -6, -6.8), 8, 8)
                # Thread
                painter.setPen(QPen(QColor(45, 38, 30, 30), 1.5, Qt.DashLine))
                painter.drawRoundedRect(card_rect.adjusted(6, 6, -6, -6), 8, 8)
            else:
                # Standard dashed border
                painter.setPen(QPen(QColor(0, 0, 0, 15), 1.5, Qt.DashLine))
                painter.drawRoundedRect(card_rect.adjusted(6, 6, -6, -6), 8, 8)
            
        if self.has_progress:
            p_rect = card_rect.adjusted(16, card_rect.height() - 22, -16, -14)
            painter.setPen(Qt.NoPen)
            
            if self.finish == "full":
                # Debossed track channel
                painter.setBrush(QColor(255, 255, 255, 200))
                painter.drawRoundedRect(p_rect.translated(0, 0.8), 2, 2)
                painter.setBrush(QColor(0, 0, 0, 30))
                painter.drawRoundedRect(p_rect.translated(0, -0.5), 2, 2)
                painter.setBrush(QColor(45, 38, 30, 15))
                painter.drawRoundedRect(p_rect, 2, 2)
                
                p_val_w = p_rect.width() * self.progress_val
                if p_val_w > 2:
                    # Gold foil hot stamp gradient
                    gold_foil = QLinearGradient(p_rect.x(), 0, p_rect.x() + p_val_w, 0)
                    gold_foil.setColorAt(0.0, QColor(180, 140, 30))
                    gold_foil.setColorAt(0.35, QColor(225, 195, 80))  # reflection highlight
                    gold_foil.setColorAt(0.6, QColor(201, 162, 39))
                    gold_foil.setColorAt(1.0, QColor(160, 120, 20))
                    
                    painter.setBrush(gold_foil)
                    painter.drawRoundedRect(QRectF(p_rect.x(), p_rect.y(), p_val_w, p_rect.height()), 2, 2)
            else:
                # Standard V14-Light flat progress bar
                painter.setBrush(QColor(230, 230, 235))
                painter.drawRoundedRect(p_rect, 2, 2)
                
                p_val_w = p_rect.width() * self.progress_val
                if p_val_w > 2:
                    painter.setBrush(QColor(201, 162, 39)) # TEKIRA Gold chunk
                    painter.drawRoundedRect(QRectF(p_rect.x(), p_rect.y(), p_val_w, p_rect.height()), 2, 2)
                
        if self.draw_text:
            painter.setPen(QColor(29, 29, 31))
            font = painter.font()
            font.setFamily("Georgia")
            font.setPixelSize(22)
            font.setBold(True)
            font.setLetterSpacing(QFont.AbsoluteSpacing, -0.5)
            painter.setFont(font)
            painter.drawText(card_rect.adjusted(30, 40, -30, -30), Qt.AlignLeft, "Restauración de Textos")
            
            font.setFamily("-apple-system, BlinkMacSystemFont, Segoe UI")
            font.setPixelSize(12)
            font.setBold(False)
            font.setLetterSpacing(QFont.AbsoluteSpacing, 1)
            painter.setFont(font)
            painter.setPen(QColor(110, 110, 115))
            painter.drawText(card_rect.adjusted(30, 75, -30, -30), Qt.AlignLeft, "EXPLORACIÓN Y APRENDIZAJE")
        else:
            # Mode D: Pure mass placeholders
            px = card_rect.x() + 16
            py = card_rect.y() + 16
            pw1, ph1 = card_rect.width() * 0.45, 10
            pw2, ph2 = card_rect.width() * 0.3, 6
            
            if self.finish == "full":
                # Letterpress debossed placeholder block
                painter.setPen(Qt.NoPen)
                # Bottom highlight
                painter.setBrush(QColor(255, 255, 255, 150))
                painter.drawRoundedRect(px, py + 0.8, pw1, ph1, 2, 2)
                painter.drawRoundedRect(px, py + 16.8, pw2, ph2, 1.5, 1.5)
                # Top inner shadow
                painter.setBrush(QColor(15, 10, 5, 30))
                painter.drawRoundedRect(px, py - 0.5, pw1, ph1, 2, 2)
                painter.drawRoundedRect(px, py + 15.5, pw2, ph2, 1.5, 1.5)
                # Main ink body
                painter.setBrush(QColor(45, 38, 30, 24))
                painter.drawRoundedRect(px, py, pw1, ph1, 2, 2)
                painter.drawRoundedRect(px, py + 16, pw2, ph2, 1.5, 1.5)
            else:
                # Standard flat placeholders
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 0, 0, 12))
                painter.drawRoundedRect(px, py, pw1, ph1, 2, 2)
                painter.drawRoundedRect(px, py + 16, pw2, ph2, 1.5, 1.5)
            
        painter.restore()

class MainWindowLab(QMainWindow):
    def __init__(self, mode="A", finish="light"):
        super().__init__()
        self.setWindowTitle(f"Physical Canvas Lab - Mode {mode} ({finish})")
        self.mode = mode
        self.finish = finish
        
        # Override window size dynamically
        if mode == "D":
            self.resize(1200, 800)
        else:
            self.resize(1000, 650)
            
        self.bg = LivingBackground(self, finish=finish)
        self.setCentralWidget(self.bg)
        
        layout = QHBoxLayout(self.bg)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add sidebar (Mode D gets textless sidebar)
        self.sidebar = TexturedSidebar(self.bg, draw_text=(mode != "D"), finish=finish)
        layout.addWidget(self.sidebar)
        
        # Central workspace
        self.workspace = QWidget(self.bg)
        self.workspace_layout = QVBoxLayout(self.workspace)
        layout.addWidget(self.workspace)
        
        self.setup_composition()
        
    def setup_composition(self):
        m = self.mode
        
        if m == "A":
            # Mode A: Centered classical card
            self.workspace_layout.setContentsMargins(0, 0, 0, 0)
            self.workspace_layout.setAlignment(Qt.AlignCenter)
            self.card = BaseCottonCard(width=440, height=280, parent=self.workspace, draw_text=True, finish=self.finish)
            self.workspace_layout.addWidget(self.card)
            
        elif m == "B":
            # Mode B: Inspired, aligned top-left
            self.workspace_layout.setContentsMargins(48, 48, 48, 48)
            self.workspace_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            self.card = BaseCottonCard(width=500, height=220, parent=self.workspace, draw_text=True, finish=self.finish)
            self.workspace_layout.addWidget(self.card)
            
        elif m == "C":
            # Mode C: Editorial extreme vertical, aligned bottom-right
            self.workspace_layout.setContentsMargins(48, 48, 48, 60)
            self.workspace_layout.setAlignment(Qt.AlignRight | Qt.AlignBottom)
            self.card = BaseCottonCard(width=280, height=420, parent=self.workspace, draw_text=True, finish=self.finish)
            self.workspace_layout.addWidget(self.card)
            
        elif m == "D":
            # Mode D: Replicate scene composition with asymmetric editorial grid
            # Margins: 18px (so paper starts at 18 + 30 = 48px from borders)
            # Spacing: -28px (so vertical spacing between paper cards is 30 + 30 - 28 = 32px)
            self.workspace_layout.setContentsMargins(18, 18, 18, 18)
            self.workspace_layout.setSpacing(-28)
            self.workspace_layout.setAlignment(Qt.AlignTop)
            
            # 1. Header line placeholder
            header_layout = QHBoxLayout()
            # Left padding matching actual paper cards alignment
            header_layout.setContentsMargins(16, 0, 16, 0)
            p_brand = QWidget()
            p_brand.setFixedSize(120, 8)
            p_tag = QWidget()
            p_tag.setFixedSize(70, 8)
            
            if self.finish == "full":
                p_brand.setStyleSheet("background-color: rgba(45, 38, 30, 28); border-bottom: 1.0px solid rgba(255, 255, 255, 180); border-top: 0.8px solid rgba(0, 0, 0, 35); border-radius: 2px;")
                p_tag.setStyleSheet("background-color: rgba(201, 162, 39, 45); border-bottom: 1.0px solid rgba(255, 255, 255, 180); border-top: 0.8px solid rgba(0, 0, 0, 35); border-radius: 2px;")
            else:
                p_brand.setStyleSheet("background-color: rgba(0, 0, 0, 20); border-radius: 2px;")
                p_tag.setStyleSheet("background-color: rgba(201, 162, 39, 45); border-radius: 2px;")
                
            header_layout.addWidget(p_brand)
            header_layout.addStretch()
            header_layout.addWidget(p_tag)
            self.workspace_layout.addLayout(header_layout)
            
            # 2. Metrics Row (3 compact cards, 1 column each)
            metrics_layout = QHBoxLayout()
            metrics_layout.setSpacing(-44) # Paper spacing is 30 + 30 - 44 = 16px
            for _ in range(3):
                m_card = BaseCottonCard(width=337, height=160, parent=self.workspace, finish=self.finish)
                metrics_layout.addWidget(m_card)
            self.workspace_layout.addLayout(metrics_layout)
            
            # 3. Input Row (Asymmetric: Left 2 columns, Right 1 column)
            input_layout = QHBoxLayout()
            input_layout.setSpacing(-44)
            da_card = BaseCottonCard(width=630, height=280, parent=self.workspace, dashed=True, finish=self.finish)
            ti_card = BaseCottonCard(width=337, height=280, parent=self.workspace, finish=self.finish)
            input_layout.addWidget(da_card)
            input_layout.addWidget(ti_card)
            self.workspace_layout.addLayout(input_layout)
            
            # 4. Recent Documents label placeholder
            lbl_placeholder = QWidget()
            lbl_placeholder.setFixedSize(140, 8)
            if self.finish == "full":
                lbl_placeholder.setStyleSheet("background-color: rgba(45, 38, 30, 20); border-bottom: 1.0px solid rgba(255, 255, 255, 180); border-top: 0.8px solid rgba(0, 0, 0, 35); border-radius: 2px;")
            else:
                lbl_placeholder.setStyleSheet("background-color: rgba(0, 0, 0, 15); border-radius: 2px;")
                
            lbl_lay = QHBoxLayout()
            lbl_lay.setContentsMargins(16, 0, 16, 0)
            lbl_lay.addWidget(lbl_placeholder)
            lbl_lay.addStretch()
            self.workspace_layout.addLayout(lbl_lay)
            
            # 5. Documents Grid Row (3 cards, 1 column each)
            docs_layout = QHBoxLayout()
            docs_layout.setSpacing(-44)
            c1 = BaseCottonCard(width=337, height=190, parent=self.workspace, has_progress=True, progress_val=1.0, finish=self.finish)
            c2 = BaseCottonCard(width=337, height=190, parent=self.workspace, has_progress=True, progress_val=0.4, finish=self.finish)
            c3 = BaseCottonCard(width=337, height=190, parent=self.workspace, has_progress=True, progress_val=0.0, finish=self.finish)
            docs_layout.addWidget(c1)
            docs_layout.addWidget(c2)
            docs_layout.addWidget(c3)
            self.workspace_layout.addLayout(docs_layout)

if __name__ == "__main__":
    mode_arg = "A"
    finish_arg = "light"
    if len(sys.argv) > 1:
        mode_arg = sys.argv[1].upper()
        if mode_arg not in ["A", "B", "C", "D"]:
            mode_arg = "A"
            
    if len(sys.argv) > 2:
        finish_arg = sys.argv[2].lower()
        if finish_arg not in ["light", "sidebar_bg", "full"]:
            finish_arg = "light"
            
    app = QApplication(sys.argv)
    window = MainWindowLab(mode=mode_arg, finish=finish_arg)
    window.show()
    sys.exit(app.exec())
