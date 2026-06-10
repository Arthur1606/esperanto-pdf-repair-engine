import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw

# Add project folder to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
project_root = Path("/Users/juannicolasrianobeltrab/Documents/esperanto-pdf-repair")
sys.path.append(str(project_root))

artifacts_dir = Path("/Users/juannicolasrianobeltrab/.gemini/antigravity-ide/brain/f6d60180-6c43-4c0a-b872-033d0930cf76")

def compose_comparison():
    mockup_path = artifacts_dir / "dashboard_spatial_mockup_1781063960288.png"
    lab_path = artifacts_dir / "lab_opt_D.png"
    
    if not mockup_path.exists() or not lab_path.exists():
        print("Required files not found")
        return
        
    img_mockup = Image.open(mockup_path)
    img_lab = Image.open(lab_path)
    
    h_target = 600
    mock_w = int(img_mockup.width * h_target / img_mockup.height)
    lab_w = int(img_lab.width * h_target / img_lab.height)
    
    img_mock_resized = img_mockup.resize((mock_w, h_target))
    img_lab_resized = img_lab.resize((lab_w, h_target))
    
    w_total = mock_w + lab_w + 40
    h_total = h_target + 80
    
    comp = Image.new("RGBA", (w_total, h_total), (245, 244, 240, 255))
    comp.paste(img_mock_resized, (15, 60))
    comp.paste(img_lab_resized, (mock_w + 25, 60))
    
    draw = ImageDraw.Draw(comp)
    draw.text((20, 20), "MOCKUP APROBADO (Izquierda)   <--->   V-D: RÉPLICA BRUTAL DE ESCENA (Derecha - Composición Pura)", fill=(29, 29, 31, 255))
    
    out_path = artifacts_dir / "lab_opt_D_vs_mockup.png"
    comp.save(out_path)
    print(f"Direct scene D comparison saved to: {out_path}")

if __name__ == "__main__":
    compose_comparison()
