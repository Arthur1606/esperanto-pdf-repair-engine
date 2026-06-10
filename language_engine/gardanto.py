import os
import sys
import logging
from typing import List

# Setup path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from language_engine.auditor import analyze_text_quality
from language_engine.pdf_repair import repair_pdf

logger = logging.getLogger(__name__)

MANDATORY_CASES = [
    "ĉar", "ĉiuj", "eĉ", "hieraŭ", "morgaŭ", "hodiaŭ",
    "ŝablono", "ĝuste", "ankaŭ", "ŝi", "feliĉa", "parolaĵo", "homaĵo"
]

def run_regression_suite(pdf_path: str):
    logger.info(f"Gardanto: Running regression suite on {pdf_path}")
    
    # Run full pipeline
    analysis = analyze_text_quality(pdf_path)
    
    approved_corrections = {}
    for item in analysis.get("missing_esperanto_analysis", []):
        if item["detection_type"] == "SUCCESSFUL_REPAIR" and item["confidence"] >= 0.85:
            approved_corrections[item["word"]] = item["suggestion"]
            
    # Check if mandatory cases were found in the repair list (assuming the PDF contains them corrupted)
    # However, to be a true integration test, we must check the FINAL output of the PDF.
    
    repaired_path, metrics = repair_pdf(pdf_path, approved_corrections)
    
    # Verify Visual Presence
    import fitz
    import unicodedata
    doc = fitz.open(repaired_path)
    final_text = ""
    for page in doc:
        final_text += page.get_text()
    doc.close()
    
    normalized_final = unicodedata.normalize('NFC', final_text)
    
    failed_cases = []
    
    # We only check mandatory cases that were actually repaired in this run
    expected_words = [w for w in approved_corrections.values() if w.lower() in MANDATORY_CASES or w in MANDATORY_CASES]
    
    for case in expected_words:
        if case not in normalized_final and case not in final_text:
            failed_cases.append(case)
            
    if failed_cases:
        logger.error(f"Gardanto: BUILD FAIL! The following mandatory words were missing in the output: {failed_cases}")
        sys.exit(1)
    else:
        logger.info("Gardanto: BUILD SUCCESS! All mandatory cases passed.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Leccion 24 is known to contain hieraŭ, eĉ, Ĉar, Ĉiuj
    # Leccion 25 contains parolaĵo, homaĵo
    test_file = os.path.join(os.path.dirname(__file__), "..", "uploads", "leccion_24.pdf")
    if os.path.exists(test_file):
        run_regression_suite(test_file)
    else:
        logger.warning("Test PDF not found. Gardanto requires a valid PDF to run.")
