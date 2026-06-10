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

finishes = ["light", "sidebar_bg", "full"]
windows = {}
paths = {}
current_index = 0

def process_next():
    global current_index
    if current_index >= len(finishes):
        compose_strip()
        app.quit()
        return
        
    finish = finishes[current_index]
    print(f"Initializing Experiment with Finish: {finish}...")
    
    # Create window in Mode D (the frozen composition)
    win = MainWindowLab(mode="D", finish=finish)
    windows[finish] = win
    win.show()
    
    # Let layout settle
    QApplication.processEvents()
    
    def perform_grab(f=finish, w=win):
        global current_index
        p = artifacts_dir / f"lab_opt_D_{f}.png"
        w.grab().save(str(p))
        paths[f] = p
        print(f"Captured Finish {f} to {p}")
        w.close()
        
        current_index += 1
        QTimer.singleShot(500, process_next)
        
    QTimer.singleShot(600, perform_grab)

def compose_strip():
    mockup_path = artifacts_dir / "dashboard_spatial_mockup_1781063960288.png"
    prev_path = artifacts_dir / "previous_lab_opt_D.png"
    
    if not mockup_path.exists():
        print(f"Mockup not found at {mockup_path}")
        return
    if not prev_path.exists():
        print(f"Previous D capture not found at {prev_path}")
        # Use light capture as previous if not found
        prev_path = paths.get("light")
        
    # Open images
    img_mockup = Image.open(mockup_path)
    img_prev = Image.open(prev_path)
    img_sidebar_bg = Image.open(paths["sidebar_bg"])
    img_full = Image.open(paths["full"])
    
    # Resize all to height 450
    h_target = 450
    
    def get_resized(img):
        w = int(img.width * h_target / img.height)
        return img.resize((w, h_target))
        
    res_prev = get_resized(img_prev)
    res_sidebar_bg = get_resized(img_sidebar_bg)
    res_full = get_resized(img_full)
    res_mockup = get_resized(img_mockup)
    
    # Calculate spacing and sizes
    gap = 20
    w_total = res_prev.width + res_sidebar_bg.width + res_full.width + res_mockup.width + (gap * 5)
    h_total = h_target + 90
    
    # Create collage
    collage = Image.new("RGBA", (w_total, h_total), (245, 244, 240, 255))
    draw = ImageDraw.Draw(collage)
    
    x_offset = gap
    images_to_paste = [
        (res_prev, "1. CAPTURA ANTERIOR (V14-Light Base)"),
        (res_sidebar_bg, "2. EXP-1 (Solo Sidebar + Fondo)"),
        (res_full, "3. EXP-2 (Full: Sidebar + Fondo + Tarjetas)"),
        (res_mockup, "4. MOCKUP DE REFERENCIA")
    ]
    
    for img, label in images_to_paste:
        collage.paste(img, (x_offset, 60))
        # Draw label
        draw.text((x_offset + 10, 25), label, fill=(29, 29, 31, 255))
        x_offset += img.width + gap
        
    out_path = artifacts_dir / "lab_experiments_comparison.png"
    collage.save(out_path)
    print(f"Experiments comparison collage saved at: {out_path}")

QTimer.singleShot(100, process_next)
sys.exit(app.exec())
