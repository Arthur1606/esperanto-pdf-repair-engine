"""
Sidebar — Esperanto Language Suite
Collapsible navigation with brand identity.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from gui.animations import create_slide_width
from gui.styles.design_system import TDS


class Sidebar(QWidget):
    item_selected = Signal(str)

    ITEMS = [
        ("dashboard", "Dashboard"),
        ("library",   "Biblioteca"),
        ("learning",  "Aprendizaje"),
        ("history",   "Historial"),
    ]
    BOTTOM_ITEMS = [
        ("settings",  "Configuración"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.expanded = True
        self.active_id = "dashboard"
        self.setFixedWidth(220)
        self.setObjectName("Sidebar")
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 20, 14, 20)
        layout.setSpacing(4)

        # ── Brand ──────────────────────────────────────
        self.brand_label = QLabel("ESPERANTO")
        self.brand_label.setObjectName("SidebarBrand")
        layout.addWidget(self.brand_label)

        layout.addSpacing(20)

        # ── Toggle ─────────────────────────────────────
        self.btn_toggle = QPushButton("◀")
        self.btn_toggle.setObjectName("SidebarToggle")
        self.btn_toggle.setFixedSize(28, 28)
        self.btn_toggle.clicked.connect(self.toggle)
        layout.addWidget(self.btn_toggle, 0, Qt.AlignLeft)

        layout.addSpacing(16)

        # ── Search Button (Cmd+K Representation) ───────
        self.search_btn = QPushButton("🔍 Buscar...         ⌘K")
        self.search_btn.setObjectName("SidebarSearch")
        self.search_btn.setCursor(Qt.PointingHandCursor)
        self.search_btn.setFixedHeight(36)
        layout.addWidget(self.search_btn)

        layout.addSpacing(12)

        # ── Nav Items ──────────────────────────────────
        self.buttons = {}
        for id_str, text in self.ITEMS:
            self._add_item(id_str, text)

        layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        for id_str, text in self.BOTTOM_ITEMS:
            self._add_item(id_str, text)

        # ── User Profile ───────────────────────────────
        self.profile_widget = QWidget()
        self.profile_widget.setObjectName("SidebarProfile")
        profile_layout = QHBoxLayout(self.profile_widget)
        profile_layout.setContentsMargins(8, 8, 8, 8)
        profile_layout.setSpacing(10)

        self.avatar_label = QLabel("T")
        self.avatar_label.setObjectName("SidebarAvatar")
        self.avatar_label.setFixedSize(32, 32)
        self.avatar_label.setAlignment(Qt.AlignCenter)

        name_layout = QVBoxLayout()
        name_layout.setSpacing(2)
        name_layout.setContentsMargins(0, 0, 0, 0)

        self.username_label = QLabel("Tekira Editor")
        self.username_label.setObjectName("SidebarUsername")
        self.user_role_label = QLabel("Principal")
        self.user_role_label.setObjectName("SidebarUserRole")

        name_layout.addWidget(self.username_label)
        name_layout.addWidget(self.user_role_label)

        profile_layout.addWidget(self.avatar_label)
        profile_layout.addLayout(name_layout)

        layout.addWidget(self.profile_widget)

        self._update_active_style()

    def _add_item(self, id_str: str, text: str):
        btn = QPushButton(text)
        btn.setObjectName("SidebarBtn")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._on_click(id_str))
        self.buttons[id_str] = {"btn": btn, "full_text": text}
        self.layout().addWidget(btn)

    def _on_click(self, id_str: str):
        self.active_id = id_str
        self._update_active_style()
        self.item_selected.emit(id_str)

    def _update_active_style(self):
        for key, data in self.buttons.items():
            if key == self.active_id:
                data["btn"].setObjectName("SidebarBtnActive")
            else:
                data["btn"].setObjectName("SidebarBtn")
            data["btn"].style().unpolish(data["btn"])
            data["btn"].style().polish(data["btn"])

    def toggle(self):
        self.expanded = not self.expanded
        start_w = 220 if not self.expanded else 64
        end_w = 64 if not self.expanded else 220

        if not self.expanded:
            self.btn_toggle.setText("▶")
            self.brand_label.hide()
            self.search_btn.hide()
            self.profile_widget.hide()
            for d in self.buttons.values():
                d["btn"].setText("")
        
        self.anim = create_slide_width(self, start_w, end_w, TDS.ANIM_NORMAL)
        if self.expanded:
            def _restore():
                self.btn_toggle.setText("◀")
                self.brand_label.show()
                self.search_btn.show()
                self.profile_widget.show()
                for d in self.buttons.values():
                    d["btn"].setText(d["full_text"])
            self.anim.finished.connect(_restore)
        self.anim.start()
