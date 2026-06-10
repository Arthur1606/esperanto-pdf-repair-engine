from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PySide6.QtWidgets import QGraphicsOpacityEffect

def create_fade_in(widget, duration=250):
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(0)
    anim.setEndValue(1)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    return anim, effect

def create_slide_width(widget, start, end, duration=250):
    anim = QPropertyAnimation(widget, b"maximumWidth")
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(QEasingCurve.InOutCubic)
    
    anim2 = QPropertyAnimation(widget, b"minimumWidth")
    anim2.setDuration(duration)
    anim2.setStartValue(start)
    anim2.setEndValue(end)
    anim2.setEasingCurve(QEasingCurve.InOutCubic)
    
    group = QParallelAnimationGroup()
    group.addAnimation(anim)
    group.addAnimation(anim2)
    return group
