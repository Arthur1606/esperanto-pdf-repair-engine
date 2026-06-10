from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QLineEdit
from PySide6.QtCore import Qt, Signal
from gui.models import DocumentJob, ReviewItem

class CandidateButton(QPushButton):
    def __init__(self, text, score):
        super().__init__(text)
        self.setObjectName("CandidateBtn")
        self.score = score
        self.setToolTip(f"Confianza de TEKIRA: {score*100:.1f}%")

class ReviewPanel(QWidget):
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.job = None
        self.current_idx = 0
        self.items = []
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        btn_back = QPushButton("← Volver")
        btn_back.setObjectName("SecondaryBtn")
        btn_back.clicked.connect(self.back_requested.emit)
        
        self.lbl_progress = QLabel("0 / 0")
        self.lbl_progress.setStyleSheet("color: #858585; font-weight: bold; font-size: 14px;")
        
        header.addWidget(btn_back)
        header.addStretch()
        header.addWidget(self.lbl_progress)
        layout.addLayout(header)
        
        # Main Area
        self.main_area = QWidget()
        self.main_area.setObjectName("ReviewCard")
        main_layout = QVBoxLayout(self.main_area)
        main_layout.setSpacing(20)
        
        # Context block
        self.lbl_context = QLabel()
        self.lbl_context.setWordWrap(True)
        self.lbl_context.setAlignment(Qt.AlignCenter)
        self.lbl_context.setStyleSheet("font-size: 18px; line-height: 1.5; color: #a0a0a0;")
        main_layout.addWidget(self.lbl_context)
        
        # Target word
        self.lbl_target = QLabel()
        self.lbl_target.setAlignment(Qt.AlignCenter)
        self.lbl_target.setStyleSheet("font-size: 36px; font-weight: 800; color: #ffffff;")
        main_layout.addWidget(self.lbl_target)
        
        # Explanation
        expl_box = QWidget()
        expl_box.setObjectName("ExplanationBox")
        expl_layout = QVBoxLayout(expl_box)
        self.lbl_explanation = QLabel("TEKIRA detectó múltiples candidatos viables. Por favor selecciona la interpretación correcta.")
        self.lbl_explanation.setWordWrap(True)
        self.lbl_explanation.setStyleSheet("color: #5E5CE6; font-size: 14px;")
        expl_layout.addWidget(self.lbl_explanation)
        main_layout.addWidget(expl_box)
        
        # Candidates layout
        self.candidates_layout = QHBoxLayout()
        main_layout.addLayout(self.candidates_layout)
        
        # Manual Input
        manual_layout = QHBoxLayout()
        self.input_manual = QLineEdit()
        self.input_manual.setPlaceholderText("Otra corrección...")
        self.input_manual.setObjectName("TextInput")
        btn_manual = QPushButton("Aplicar")
        btn_manual.setObjectName("PrimaryBtn")
        btn_manual.clicked.connect(lambda: self.resolve_current(self.input_manual.text()))
        manual_layout.addWidget(self.input_manual)
        manual_layout.addWidget(btn_manual)
        main_layout.addLayout(manual_layout)
        
        layout.addWidget(self.main_area)
        
        # Controls
        controls = QHBoxLayout()
        btn_skip = QPushButton("Saltar (Ignorar)")
        btn_skip.setObjectName("SecondaryBtn")
        btn_skip.clicked.connect(lambda: self.resolve_current(self.items[self.current_idx].original_word))
        controls.addWidget(btn_skip, 0, Qt.AlignCenter)
        layout.addLayout(controls)

    def load_job(self, job: DocumentJob):
        self.job = job
        if not job.result or not job.result.items:
            self.items = []
        else:
            # Filter unresolved
            self.items = [it for it in job.result.items if not it.is_resolved]
        
        self.current_idx = 0
        self.render_current()

    def render_current(self):
        if not self.items or self.current_idx >= len(self.items):
            self.lbl_context.setText("¡Todo revisado!")
            self.lbl_target.setText("✅")
            self.lbl_progress.setText("Completado")
            self.main_area.hide()
            return
            
        self.main_area.show()
        item = self.items[self.current_idx]
        self.lbl_progress.setText(f"{self.current_idx + 1} / {len(self.items)}")
        self.lbl_target.setText(item.original_word)
        
        # Highlight original word in context
        ctx = item.context.replace(item.original_word, f'<span style="color: #ffffff; font-weight: bold;">{item.original_word}</span>')
        self.lbl_context.setText(f"...{ctx}...")
        
        # Clear candidates
        while self.candidates_layout.count():
            child = self.candidates_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        for cand in item.candidates:
            w = cand["word"]
            btn = CandidateButton(w, cand["score"])
            # Default param binding trick
            btn.clicked.connect(lambda checked=False, w=w: self.resolve_current(w))
            self.candidates_layout.addWidget(btn)
            
        self.input_manual.clear()

    def resolve_current(self, word):
        if not word.strip() or self.current_idx >= len(self.items): return
        item = self.items[self.current_idx]
        item.resolved_word = word
        item.is_resolved = True
        self.current_idx += 1
        self.render_current()
