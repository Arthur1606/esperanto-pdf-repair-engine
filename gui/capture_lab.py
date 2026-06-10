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

window = MainWindowLab()
window.resize(1000, 650)
window.show()

artifacts_dir = Path("/Users/juannicolasrianobeltrab/.gemini/antigravity-ide/brain/9e875e0b-1136-4b8e-a8ec-3b52bc706cad")

def do_capture():
    try:
        # Process pending draw events
        QApplication.processEvents()
        
        lab_capture_path = artifacts_dir / "physical_canvas_lab_capture.png"
        window.grab().save(str(lab_capture_path))
        print(f"Captured laboratory screen to: {lab_capture_path}")
        
        compose_comparison(lab_capture_path)
    finally:
        app.quit()

def compose_comparison(lab_path):
    mockup_path = artifacts_dir / "dashboard_spatial_mockup_1781063960288.png"
    if not mockup_path.exists():
        print(f"Mockup not found at {mockup_path}")
        return
        
    img_mockup = Image.open(mockup_path)
    img_lab = Image.open(lab_path)
    
    # Resize to height 500 for comparison
    h_target = 500
    mock_w = int(img_mockup.width * h_target / img_mockup.height)
    lab_w = int(img_lab.width * h_target / img_lab.height)
    
    img_mock_resized = img_mock_pattern = img_mockup.resize((mock_w, h_target))
    img_lab_resized = img_lab.resize((lab_w, h_target))
    
    w_total = mock_w + lab_w + 40
    h_total = h_target + 80
    
    comp = Image.new("RGBA", (w_total, h_total), (245, 244, 240, 255))
    comp.paste(img_mock_resized, (15, 60))
    comp.paste(img_lab_resized, (mock_w + 25, 60))
    
    draw = ImageDraw.Draw(comp)
    draw.text((20, 20), "MOCKUP APROBADO (Izquierda)   <--->   PHYSICAL CANVAS LAB (Derecha)", fill=(29, 29, 31, 255))
    
    out_path = artifacts_dir / "physical_canvas_lab_comparison.png"
    comp.save(out_path)
    print(f"Composed comparison saved to: {out_path}")

QTimer.singleShot(1500, do_capture)
sys.exit(app.exec())
