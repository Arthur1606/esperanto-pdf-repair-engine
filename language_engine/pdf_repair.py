import fitz
import os
import time
import io
import logging

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
    font_path = os.path.join(os.path.dirname(__file__), '..', 'NotoSans-Regular.ttf')
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

        # Apply corrections using search_for to preserve punctuation and precisely locate words
        for original, suggestion in correction_map.items():
            rects = page.search_for(original)
            for rect in rects:
                candidates_found += 1
                executed_replacements += 1
                
                # Expand the redaction rect slightly to fully erase any overlapping pixels
                # but keep the original rect for insertion
                redact_rect = rect + (-1, -1, 1, 1)
                
                # Apply redaction
                page.add_redact_annot(redact_rect, text="", fill=None)
                page.apply_redactions(images=0)
                
                # Calculate approx_fontsize based on original rect height
                approx_fontsize = rect.height * 0.8
                
                # Expand rect exclusively for insertion layout to bypass strict PyMuPDF bounds
                # We give infinite horizontal space and extra downward vertical space (for descenders)
                fit_rect = fitz.Rect(rect.x0, rect.y0, rect.x1 + 100, rect.y1 + rect.height)
                
                # Phase 4 & 5: Arhitekto & Rigardanto
                from language_engine.rigardanto import verify_visual_insertion
                from language_engine.biblioteko import biblioteko
                
                # 1. Redact Original
                page.add_redact_annot(rect, fill=(1, 1, 1))
                page.apply_redactions()
                
                # 2. Insert with Arhitekto
                # We expand the rect slightly if needed, but the original rect is standard
                # We use search_for logic (which we already did to find 'rect')
                
                max_retries = 2
                inserted_successfully = False
                
                current_rect = fit_rect
                for attempt in range(max_retries):
                    res = page.insert_textbox(
                        current_rect,
                        suggestion,
                        fontname="Roboto-Regular",
                        fontfile=font_path,
                        fontsize=approx_fontsize,
                        color=(0, 0, 0),
                        align=0
                    )
                    
                    if res >= 0:
                        # 3. Rigardanto Verification
                        is_valid_visually = verify_visual_insertion(page, current_rect)
                        if is_valid_visually:
                            inserted_successfully = True
                            # FASE 3: Memoro - Record successful correction!
                            # Assuming a standard high confidence for now since it reached layout engine
                            biblioteko.record_correction(original, suggestion, 0.90)
                            break
                        else:
                            logging.warning(f"Rigardanto rejected insertion for '{suggestion}'. Retrying with expanded rect...")
                            # Fallback: Expand rect to give more space
                            current_rect = fitz.Rect(current_rect.x0, current_rect.y0 - 2, current_rect.x1 + 5, current_rect.y1 + 2)
                            # We need to re-redact because the failed insertion is still there!
                            page.add_redact_annot(current_rect, fill=(1, 1, 1))
                            page.apply_redactions()
                    else:
                        # If insert_textbox fails natively (text doesn't fit at all)
                        current_rect = fitz.Rect(current_rect.x0, current_rect.y0 - 2, current_rect.x1 + 5, current_rect.y1 + 2)
                        
                if not inserted_successfully:
                    logging.error(f"Arhitekto failed to insert '{suggestion}' visually after retries.")
                
                method_used = "arhitekto+rigardanto"
                insertion_info = f"rect: {current_rect} (success={inserted_successfully})"
                
                detailed_log.append({
                    "original": original,
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
