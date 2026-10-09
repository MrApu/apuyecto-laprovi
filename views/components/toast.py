from typing import Optional
from PySide6.QtWidgets import QWidget, QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QFont, QColor

class ToastNotification(QFrame):
    """
    Notificación flotante moderna (Toast) no bloqueante con animación de entrada y auto-cierre.
    """
    def __init__(self, message: str, toast_type: str = "success", duration_ms: int = 3000, parent: Optional[QWidget] = None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.duration_ms = duration_ms
        self.toast_type = toast_type.lower()
        self._init_ui(message)

    def _init_ui(self, message: str):
        # Color mapping
        themes = {
            "success": ("#064E3B", "#10B981", "#34D399", "✅"),
            "info": ("#164E63", "#06B6D4", "#67E8F9", "ℹ️"),
            "warning": ("#78350F", "#F59E0B", "#FCD34D", "⚠️"),
            "error": ("#881337", "#F43F5E", "#FDA4AF", "❌"),
        }
        bg_col, border_col, txt_col, icon = themes.get(self.toast_type, themes["info"])

        self.setStyleSheet(f"""
            QFrame {{
                background-color: #0F172A;
                border-left: 4px solid {border_col};
                border-top: 1px solid #1E293B;
                border-right: 1px solid #1E293B;
                border-bottom: 1px solid #1E293B;
                border-radius: 8px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 16px; background: transparent;")
        layout.addWidget(lbl_icon)

        lbl_msg = QLabel(message)
        lbl_msg.setStyleSheet(f"color: #F8FAFC; font-size: 12px; font-weight: 700; background: transparent;")
        lbl_msg.setWordWrap(True)
        layout.addWidget(lbl_msg, 1)

        btn_close = QPushButton("✕")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94A3B8;
                font-size: 12px;
                font-weight: bold;
                border: none;
                padding: 2px 6px;
            }
            QPushButton:hover {
                color: #FFFFFF;
            }
        """)
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.close)

    def show_toast(self, parent_widget: Optional[QWidget] = None):
        self.adjustSize()
        if parent_widget:
            # Position at bottom right of parent window
            parent_rect = parent_widget.rect()
            global_pos = parent_widget.mapToGlobal(QPoint(
                parent_rect.width() - self.width() - 25,
                parent_rect.height() - self.height() - 25
            ))
            self.move(global_pos)
        self.show()
        self.timer.start(self.duration_ms)


class ToastManager:
    _current_toast: Optional[ToastNotification] = None

    @classmethod
    def show_success(cls, message: str, parent: Optional[QWidget] = None):
        cls.show(message, "success", 3000, parent)

    @classmethod
    def show_info(cls, message: str, parent: Optional[QWidget] = None):
        cls.show(message, "info", 3000, parent)

    @classmethod
    def show_warning(cls, message: str, parent: Optional[QWidget] = None):
        cls.show(message, "warning", 3500, parent)

    @classmethod
    def show_error(cls, message: str, parent: Optional[QWidget] = None):
        cls.show(message, "error", 4000, parent)

    @classmethod
    def show(cls, message: str, toast_type: str = "info", duration_ms: int = 3000, parent: Optional[QWidget] = None):
        if cls._current_toast:
            try:
                cls._current_toast.close()
            except Exception:
                pass
        cls._current_toast = ToastNotification(message, toast_type, duration_ms, parent)
        cls._current_toast.show_toast(parent)
