from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, Signal
from gui.animations import create_slide_width

class Sidebar(QWidget):
    item_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.expanded = True
        self.setFixedWidth(200)
        self.setObjectName("Sidebar")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(5)
        
        # Toggle btn
        self.btn_toggle = QPushButton("☰")
        self.btn_toggle.setObjectName("SidebarToggle")
        self.btn_toggle.setFixedSize(30, 30)
        self.btn_toggle.clicked.connect(self.toggle)
        layout.addWidget(self.btn_toggle, 0, Qt.AlignLeft)
        
        layout.addSpacing(20)
        
        self.buttons = {}
        self.add_item("dashboard", "⌘ Mission Control")
        self.add_item("library", "📚 Biblioteca")
        self.add_item("learning", "🌱 Aprendizaje")
        self.add_item("history", "🕒 Historial")
        
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.add_item("settings", "⚙ Configuración")

    def add_item(self, id_str, text):
        btn = QPushButton(text)
        btn.setObjectName("SidebarBtn")
        btn.clicked.connect(lambda: self.item_selected.emit(id_str))
        self.buttons[id_str] = {"btn": btn, "full_text": text, "icon": text.split(' ')[0]}
        self.layout().addWidget(btn)

    def toggle(self):
        self.expanded = not self.expanded
        start_w = 200 if not self.expanded else 60
        end_w = 60 if not self.expanded else 200
        
        if not self.expanded:
            for d in self.buttons.values():
                d["btn"].setText(d["icon"])
        
        self.anim = create_slide_width(self, start_w, end_w, 200)
        if self.expanded:
            self.anim.finished.connect(lambda: [d["btn"].setText(d["full_text"]) for d in self.buttons.values()])
        self.anim.start()
