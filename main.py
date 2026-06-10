import sys
import os
import json
import logging
from pathlib import Path

# Añadir directorio actual al path para importar language_engine
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from gui.styles.theme_generator import generate_stylesheet

def setup_logging():
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "studio.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_config():
    config_path = Path(__file__).parent / "config" / "settings.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def main():
    setup_logging()
    logger = logging.getLogger("studio.main")
    logger.info("Iniciando Esperanto Language Suite...")
    
    config = load_config()
    
    app = QApplication(sys.argv)
    
    # Generate stylesheet from Design System tokens
    app.setStyleSheet(generate_stylesheet())
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
