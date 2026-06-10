import fitz
import numpy as np
import logging

logger = logging.getLogger(__name__)

def verify_visual_insertion(page: fitz.Page, rect: fitz.Rect) -> bool:
    """
    Rigardanto (Visual Verification Engine)
    Verifies if the inserted text is visually present and valid.
    Returns True if visually validated, False if it detects errors (clipping, tofu, blank).
    """
    try:
        # Render the specific region to a pixmap
        # We use a high DPI (e.g., 300) to ensure accurate pixel analysis
        mat = fitz.Matrix(4, 4)  # 4x zoom for detailed pixel analysis
        pix = page.get_pixmap(clip=rect, matrix=mat, alpha=False)
        
        # Convert to numpy array (grayscale)
        pixels = np.frombuffer(pix.samples, dtype=np.uint8)
        
        # 1. Blank Check (Clipping or text completely failed to render)
        # In grayscale, 255 is white. If all pixels are very close to white, the insertion is invisible.
        if np.mean(pixels) >= 253:
            logger.warning("Rigardanto: Failed - Region is completely blank (possible clipping or invisible font).")
            return False
            
        # 2. Tofu / Missing Glyph Check (.notdef box)
        # Missing glyphs often render as hollow squares. They create a very specific 
        # high-contrast border pattern with a hollow center. 
        # Alternatively, sometimes it's a solid black rectangle.
        # If the text is a solid black box, the variance of non-white pixels is extremely low.
        non_white = pixels[pixels < 250]
        if len(non_white) > 0:
            variance = np.var(non_white)
            if variance < 5.0 and np.mean(non_white) < 50:
                logger.warning("Rigardanto: Failed - Detected potential .notdef (tofu) block or solid black box.")
                return False
                
        # 3. Floating Text Check
        # We can check if the pixels touch the absolute boundaries of the rect,
        # which would imply the text overflowed its bounding box.
        # For now, if variance is healthy and it's not blank, we approve.
        
        return True
    except Exception as e:
        logger.error(f"Rigardanto encountered an error during verification: {e}")
        return False
