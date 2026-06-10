import glob
import os
import sys
import re

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.services.auditor import analyze_text_quality

files = sorted(glob.glob(os.path.join(os.path.dirname(__file__), '..', 'uploads', 'leccion_*.pdf')))
mr_cases = []

print("Extracting MR cases...")
for f in files:
    try:
        res = analyze_text_quality(f)
        for item in res.get("missing_esperanto_analysis", []):
            if item["detection_type"] == "Jugxanto_ManualReview":
                for _ in range(item["count"]):
                    mr_cases.append({
                        "word": item["word"],
                        "candidates": item["ambiguous_candidates"],
                        "snippet": item["snippet"]
                    })
    except Exception as e:
        print(f"Error {f}: {e}")

categories = {
    "vocabulario/conjugacion": 0,
    "bilingue_espanol": 0,
    "ambiguedad_real": 0,
    "ocr_error": 0
}

spanish_stop = {"el", "la", "los", "las", "un", "una", "de", "para", "por", "con", "y", "o", "él", "ella", "ello", "nosotros", "yo", "tú"}

print(f"Total MR cases extracted: {len(mr_cases)}")

for c in mr_cases:
    snip = c["snippet"].lower()
    words = set(re.findall(r'\b\w+\b', snip))
    
    # Check for lists/vocab: multiple verbs in a row, or parentheses like (él/ella)
    if re.search(r'\b\w+as\b \b\w+is\b \b\w+os\b', snip) or re.search(r'\b\w+i\s+\w+\s+\w+as\b', snip):
        categories["vocabulario/conjugacion"] += 1
    elif "(" in snip and "/" in snip: # (él/ella)
        categories["vocabulario/conjugacion"] += 1
    elif words.intersection(spanish_stop):
        categories["bilingue_espanol"] += 1
    elif bool(re.search(r'\d', c["word"])) or len(c["word"]) <= 2:
        categories["ocr_error"] += 1
    else:
        categories["ambiguedad_real"] += 1

print("\n--- RESULTS ---")
total = len(mr_cases)
if total > 0:
    for k, v in categories.items():
        print(f"{k}: {v} ({(v/total)*100:.1f}%)")

print("\n--- EXAMPLES ---")
for k in categories.keys():
    print(f"\n[{k}]")
    count = 0
    for c in mr_cases:
        snip = c["snippet"].lower()
        words = set(re.findall(r'\b\w+\b', snip))
        matched = False
        if k == "vocabulario/conjugacion" and (re.search(r'\b\w+as\b \b\w+is\b \b\w+os\b', snip) or "(" in snip): matched = True
        elif k == "bilingue_espanol" and words.intersection(spanish_stop): matched = True
        elif k == "ocr_error" and (bool(re.search(r'\d', c["word"])) or len(c["word"]) <= 2): matched = True
        elif k == "ambiguedad_real": matched = True
        
        if matched:
            print(f"Word: {c['word']} -> {c['candidates']}\nSnippet: {c['snippet']}")
            count += 1
            if count >= 3: break
