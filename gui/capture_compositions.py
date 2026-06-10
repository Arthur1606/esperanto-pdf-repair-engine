import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt
from PIL import Image, ImageDraw

# Add project folder to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
project_root = Path("/Users/juannicolasrianobeltrab/Documents/esperanto-pdf-repair")
sys.path.append(str(project_root))

from gui.physical_canvas_lab import MainWindowLab

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

artifacts_dir = Path("/Users/juannicolasrianobeltrab/.gemini/antigravity-ide/brain/f6d60180-6c43-4c0a-b872-033d0930cf76")

# We will instantiate and capture windows sequentially with QTimer delays
windows = {}
paths = {}
modes = ["A", "B", "C", "D"]
current_index = 0

def process_next():
    global current_index
    if current_index >= len(modes):
        compose_grid()
        app.quit()
        return
        
    mode = modes[current_index]
    print(f"Initializing Mode {mode}...")
    
    # Create window
    win = MainWindowLab(mode=mode)
    windows[mode] = win
    win.show()
    
    # Let layout settle
    QApplication.processEvents()
    
    # Delay capture to allow paint events to draw properly
    def perform_grab(m=mode, w=win):
        global current_index
        p = artifacts_dir / f"lab_opt_{m}.png"
        w.grab().save(str(p))
        paths[m] = p
        print(f"Captured Option {m} to {p}")
        w.close()
        
        # Advance to next phase
        current_index += 1
        QTimer.singleShot(400, process_next)
        
    QTimer.singleShot(400, perform_grab)

def compose_grid():
    images = {key: Image.open(p) for key, p in paths.items()}
    
    # Resize to standard widths for the 2x2 grid
    # Mode D is 1200x800, others are 1000x650.
    # We will resize all to width 500 (preserving aspect ratio)
    w_target = 500
    resized_imgs = {}
    for key, img in images.items():
        h_target = int(img.height * w_target / img.width)
        resized_imgs[key] = img.resize((w_target, h_target))
        
    w_total = w_target * 2 + 45
    # Since A, B, C have height ~325, and D has height ~333,
    # we can use the max height of the first row to align the second row
    h_row1 = max(resized_imgs["A"].height, resized_imgs["B"].height)
    h_row2 = max(resized_imgs["C"].height, resized_imgs["D"].height)
    h_total = h_row1 + h_row2 + 120
    
    grid = Image.new("RGBA", (w_total, h_total), (245, 244, 240, 255))
    draw = ImageDraw.Draw(grid)
    
    # Position mappings
    pos = {
        "A": (15, 45),
        "B": (w_target + 30, 45),
        "C": (15, h_row1 + 90),
        "D": (w_target + 30, h_row1 + 90)
    }
    
    # Titles mapping
    titles = {
        "A": "V-A: Composición Simétrica (Línea Base)",
        "B": "V-B: Composición Inspirada (Grid 1:1)",
        "C": "V-C: Composición Editorial Extrema (Asimetría)",
        "D": "V-D: Réplica Brutal de Escena (Composición Pura)"
    }
    
    for key in modes:
        x, y = pos[key]
        grid.paste(resized_imgs[key], (x, y))
        draw.text((x + 10, y - 25), titles[key], fill=(29, 29, 31, 255))
        
    out_path = artifacts_dir / "lab_compositions_comparison.png"
    grid.save(out_path)
    print(f"Compositions comparison grid saved at: {out_path}")

# Start the sequence
QTimer.singleShot(100, process_next)
sys.exit(app.exec())
