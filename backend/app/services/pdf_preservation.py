import fitz
import os
import time
import io

from typing import Tuple, Dict, Any

def repair_pdf(original_pdf_path: str, approved_corrections: dict) -> Tuple[str, Dict[str, Any]]:
    """
    In-place repair engine using PyMuPDF (V2 - Whole-Word Bounding Boxes).
    Takes a dictionary of { "original_word": "suggested_word" }.
    Returns a tuple of (repaired_pdf_path, metrics_dict).
    """
    if not os.path.exists(original_pdf_path):
        raise FileNotFoundError(f"Original PDF not found at {original_pdf_path}")
    # 1. Prepare target path
    start_time = time.time()
    
    if not approved_corrections:
        # If no corrections needed, just copy the file
        import shutil
        basename = os.path.basename(original_pdf_path)
        name, ext = os.path.splitext(basename)
        repaired_path = f"uploads/{name}_repaired{ext}"
        shutil.copy2(original_pdf_path, repaired_path)
        return repaired_path, {}

    base, ext = os.path.splitext(original_pdf_path)
    repaired_path = f"{base}_repaired{ext}"

    doc_original = fitz.open(original_pdf_path)
    total_chars_original = sum(len(page.get_text()) for page in doc_original)
    doc_original.close()

    # 3. Open PDF for repair
    doc = fitz.open(original_pdf_path)
    
    # Register Noto Sans font
    font_path = os.path.join(os.path.dirname(__file__), '..', '..', 'NotoSans-Regular.ttf')
    has_noto = os.path.exists(font_path)

    # Fast lookup from approved dictionary
    correction_map = approved_corrections

    executed_replacements = 0
    candidates_found = 0
    detailed_log = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        words_info = page.get_text("words")
        
        # We need to insert the font in each page we modify
        if has_noto:
            page.insert_font(fontname="noto", fontfile=font_path)
            font_to_use = "noto"
        else:
            font_to_use = "helv" # Fallback

        # Apply corrections by iterating through words directly
        for w_info in words_info:
            wx0, wy0, wx1, wy1, w_text, block_no, line_no, word_no = w_info
            
            clean_text = w_text.strip('.,;:!?()"\'-[]{}')
            
            # Remove hidden damaged markers if any for matching, or just match exactly
            # Wait, the frontend sends original_word EXACTLY as it was extracted.
            if clean_text in correction_map:
                suggestion = correction_map[clean_text]
                rect = fitz.Rect(wx0, wy0, wx1, wy1)
                
                candidates_found += 1
                executed_replacements += 1
                
                # Apply redaction
                page.add_redact_annot(rect, text="", fill=None)
                page.apply_redactions(images=0)
                
                approx_fontsize = rect.height * 0.8
                
                # Experimental toggle
                use_insert_text = True
                
                if use_insert_text:
                    insertion_point = fitz.Point(rect.x0, rect.y1 - (rect.height * 0.2))
                    if has_noto:
                        page.insert_text(
                            insertion_point,
                            suggestion,
                            fontsize=approx_fontsize,
                            fontname="noto",
                            fontfile=font_path,
                            color=(0, 0, 0)
                        )
                    else:
                        page.insert_text(
                            insertion_point,
                            suggestion,
                            fontsize=approx_fontsize,
                            fontname="helv",
                            color=(0, 0, 0)
                        )
                    method_used = "text"
                    insertion_info = f"({insertion_point.x}, {insertion_point.y})"
                else:
                    if has_noto:
                        page.insert_textbox(
                            rect,
                            suggestion,
                            fontsize=approx_fontsize,
                            fontname="noto",
                            fontfile=font_path,
                            color=(0, 0, 0),
                            align=0
                        )
                    else:
                        page.insert_textbox(
                            rect,
                            suggestion,
                            fontsize=approx_fontsize,
                            fontname="helv",
                            color=(0, 0, 0),
                            align=0
                        )
                    method_used = "textbox"
                    insertion_info = f"rect: {rect}"
                    
                detailed_log.append({
                    "original": clean_text,
                    "corrected": suggestion,
                    "page": page_num + 1,
                    "original_bbox": [rect.x0, rect.y0, rect.x1, rect.y1],
                    "insertion_point": insertion_info,
                    "method": method_used
                })

    doc.save(repaired_path)
    doc.close()
    
    # Measure chars after and semantic validation
    doc_repaired = fitz.open(repaired_path)
    full_text_repaired = ""
    for page in doc_repaired:
        full_text_repaired += page.get_text()
    total_chars_repaired = len(full_text_repaired)
    doc_repaired.close()
    
    # Validation logic
    target_words = list(approved_corrections.values())
    unique_targets = set(target_words)
    total_expected = len(unique_targets)
    recovered_count = 0
    
    import unicodedata
    normalized_text = unicodedata.normalize('NFC', full_text_repaired)
    
    for word in unique_targets:
        if word in normalized_text or word in full_text_repaired:
            recovered_count += 1
            
    recovery_rate = min(100.0, (recovered_count / total_expected) * 100) if total_expected else 100.0
    semantic_validation_passed = recovery_rate > 95.0
    extraction_success_rate = recovery_rate # same essentially
    
    preservation_pct = min(100.0, (total_chars_repaired / total_chars_original) * 100) if total_chars_original else 0
    
    end_time = time.time()
    repair_time_ms = round((end_time - start_time) * 1000)
    
    metrics = {
        "candidates_found": candidates_found,
        "replacements_executed": executed_replacements,
        "chars_before": total_chars_original,
        "chars_after": total_chars_repaired,
        "preservation_percentage": round(preservation_pct, 2),
        "recovery_rate": round(recovery_rate, 2),
        "semantic_validation_passed": semantic_validation_passed,
        "extraction_success_rate": round(extraction_success_rate, 2),
        "repair_time_ms": repair_time_ms,
        "detailed_log": detailed_log
    }
    
    return repaired_path, metrics
