from PySide6.QtWidgets import QDialog, QGraphicsOpacityEffect
from PySide6.QtCore import QPropertyAnimation, QEasingCurve


def fade_in(dialog: QDialog, duration=300):
    """
    Aplica una animación de fade in al dialogo dado.
    """
    effect = QGraphicsOpacityEffect(dialog)
    dialog.setGraphicsEffect(effect)
    animation = QPropertyAnimation(effect, b"opacity")
    animation.setDuration(duration)
    animation.setStartValue(0)
    animation.setEndValue(1)
    animation.setEasingCurve(QEasingCurve.OutCubic)
    animation.start()
    # Guardar referencia para evitar que se destruya
    dialog._fade_animation = animation
