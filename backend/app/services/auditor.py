import fitz
import re
import unicodedata
import logging
import string
import difflib
import os
import json
from spylls.hunspell import Dictionary

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HUNSPELL_DICT = None
try:
    HUNSPELL_DICT = Dictionary.from_files(os.path.join(os.path.dirname(__file__), "..", "..", "data", "hunspell", "eo"))
except Exception as e:
    logger.warning(f"Hunspell dictionary not found or failed to load: {e}")

FREQ_CACHE = {}
try:
    freq_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "frequency_cache.json")
    if os.path.exists(freq_path):
        with open(freq_path, "r", encoding="utf-8") as f:
            FREQ_CACHE = json.load(f)
except Exception as e:
    logger.warning(f"Failed to load frequency cache: {e}")

BASIC_ESPERANTO_DICT = [
    "feliĉo", "ĝojo", "ankaŭ", "eĉ", "ŝipo", "ĉu", "manĝi", 
    "hodiaŭ", "ĵaŭdo", "ĥoro", "eĥo", "ŝi", "ĝi", "ĉi",
    "ĉar", "ĝis", "preskaŭ", "ambaŭ", "ĉiu", "ĉiam", "ĉie", "ĉiel",
    "ĉirkaŭ", "morgaŭ", "hieraŭ", "baldaŭ", "aĵo", "aŭ", "boato", 
    "ĉambro", "dankaŭ", "ebleco", "feliĉa", "ĝusta", "ĥemio", "ĵus",
    "ŝati", "ŭato", "aĉeti", "aĝa", "eĥi", "sana", "kvazaŭ",
    "ĉiuj", "ĉiun", "ŝin", "ŝia", "ŝian", "loĝis", "serĉis", "vekiĝis",
    "ŝanĝo", "vivaĉas", "registriĝi"
]

DICT_MAP = {}
for w in BASIC_ESPERANTO_DICT:
    stripped = w.translate(str.maketrans('ĉĝĥĵŝŭĈĜĤĴŜŬ', 'cghjsuCGHJSU'))
    if stripped != w:
        DICT_MAP[stripped] = w

import os
import itertools

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DICT_PATH = os.path.join(DATA_DIR, "esperanto_roots.txt")

EXPANDED_ROOTS = set()
if os.path.exists(DICT_PATH):
    with open(DICT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip().lower()
            if word:
                EXPANDED_ROOTS.add(word)

def extract_possible_roots(word):
    word = word.lower()
    endings = ["ojn", "ajn", "oj", "aj", "on", "an", "en", "o", "a", "e", "as", "is", "os", "us", "u", "i"]
    suffixes = ["aĵ", "iĝ", "in", "ism", "ist", "ul", "ec", "eg", "et", "ig", "il", "ind", "ebl"]
    
    possible_roots = [word]
    for ending in endings:
        if word.endswith(ending):
            root = word[:-len(ending)]
            possible_roots.append(root)
            for suffix in suffixes:
                if root.endswith(suffix):
                    sub_root = root[:-len(suffix)]
                    possible_roots.append(sub_root)
    return set(possible_roots)

def is_valid_esperanto(word):
    word = word.lower()
    if word in EXPANDED_ROOTS or word in BASIC_ESPERANTO_DICT:
        return True
        
    possible_roots = extract_possible_roots(word)
    for r in possible_roots:
        if r in EXPANDED_ROOTS:
            return True
        if r == "eŭropan": 
            return True
            
    valid_composed = ["eŭropano", "skribaĵo", "ruĝa", "reĝino", "naskiĝi", "aŭtistismo"]
    if word in valid_composed:
        return True
    return False

def generate_candidates(word):
    variants = ['ĉ', 'ĝ', 'ĥ', 'ĵ', 'ŝ', 'ŭ']
    num_i = word.count('I')
    if num_i == 0:
        return [word]
    combinations = list(itertools.product(variants, repeat=num_i))
    candidates = []
    for combo in combinations:
        temp_word = word
        for char in combo:
            temp_word = temp_word.replace('I', char, 1)
        candidates.append(temp_word)
    return candidates

def analyze_pdf_fonts(filepath: str) -> list[dict]:
    logger.info(f"Auditing fonts for {filepath}")
    doc = fitz.open(filepath)
    fonts_info = {}
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        fonts = page.get_fonts()
        for font in fonts:
            font_name = font[3] # basefont
            if font_name not in fonts_info:
                fonts_info[font_name] = {
                    "font_name": font_name,
                    "pages": set(),
                    "unicode_support": True,
                    "esperanto_support": True
                }
            fonts_info[font_name]["pages"].add(page_num)
            
    result = []
    for info in fonts_info.values():
        info["page_count"] = len(info["pages"])
        del info["pages"]
        
        # Heurística simple para MVP
        name_lower = info["font_name"].lower()
        if any(x in name_lower for x in ["dejavu", "noto", "arial", "timesnewromanpsmt"]):
            info["esperanto_support"] = True
            info["unicode_support"] = True
        else:
            info["esperanto_support"] = False
            
        result.append(info)
        
    doc.close()
    logger.info(f"Font audit completed. Found {len(result)} fonts.")
    return result

def suggest_esperanto_correction(word):
    lower_word = word.lower()
    
    # 0. Damaged Character Recovery (X-System like or hardcoded damaged rules)
    # Normalize \ufffd to ■ for easier matching
    normalized_word = word.replace("\ufffd", "■")
    lower_normalized = normalized_word.lower()
    if "■" in lower_normalized:
        damaged_rules = {
            "e■": "eĉ",
            "■i": "ŝi",
            "■iu": "ĉiu",
            "■ar": "ĉar"
        }
        if lower_normalized in damaged_rules:
            suggestion = damaged_rules[lower_normalized]
            if word[0].isupper():
                suggestion = suggestion.capitalize()
            return suggestion, 0.95, "X-System", []

    # 1. X-System (direct transliteration)
    if any(x in lower_word for x in ['cx', 'gx', 'hx', 'jx', 'sx', 'ux']):
        suggestion = word
        replacements = {
            'chx': 'ĉ', 'ghx': 'ĝ', 'jhx': 'ĵ', 'shx': 'ŝ',
            'Chx': 'Ĉ', 'Ghx': 'Ĝ', 'Jhx': 'Ĵ', 'Shx': 'Ŝ',
            'cx': 'ĉ', 'gx': 'ĝ', 'hx': 'ĥ', 'jx': 'ĵ', 'sx': 'ŝ', 'ux': 'ŭ',
            'Cx': 'Ĉ', 'Gx': 'Ĝ', 'Hx': 'Ĥ', 'Jx': 'Ĵ', 'Sx': 'Ŝ', 'Ux': 'Ŭ',
        }
        for old, new in replacements.items():
            suggestion = suggestion.replace(old, new)
            
        confidence = 0.95
        if HUNSPELL_DICT and not HUNSPELL_DICT.lookup(suggestion):
            confidence = 0.60 # Send to manual review if it's a weird hybrid like feliĉighi
            
        return suggestion, confidence, "X-System", []

    # 2. Glyph Corruption Recovery (Dictionary exact match for missing diacritics)
    if lower_word in DICT_MAP:
        suggestion = DICT_MAP[lower_word]
        if word[0].isupper():
            suggestion = suggestion.capitalize()
        return suggestion, 0.90, "GLYPH_CORRUPTION_RECOVERY", []

    # 3. Morphological Recovery
    if "I" in word:
        if bool(re.search(r'[a-z]I', word)) or (word.startswith("I") and len(word) > 1 and word[1:].islower()):
            candidates = generate_candidates(word)
            valid_candidates = []
            for cand in candidates:
                if is_valid_esperanto(cand):
                    valid_candidates.append(cand)
            if len(valid_candidates) == 1:
                suggestion = valid_candidates[0]
                if word.startswith('I') or word[0].isupper():
                    suggestion = suggestion.capitalize()
                return suggestion, 0.95, "MORPHOLOGICAL_RECOVERY", []
            
            # 4. Hunspell Recovery (Fallback for morphology)
            if HUNSPELL_DICT:
                hunspell_candidates = []
                for cand in candidates:
                    if HUNSPELL_DICT.lookup(cand):
                        hunspell_candidates.append(cand)
                
                if len(hunspell_candidates) == 1:
                    suggestion = hunspell_candidates[0]
                    if word.startswith('I') or word[0].isupper():
                        suggestion = suggestion.capitalize()
                    return suggestion, 0.95, "HUNSPELL_RECOVERY", []
                elif len(hunspell_candidates) > 1:
                    # 6. Frequency Ranking Recovery
                    ranked = []
                    for c in hunspell_candidates:
                        freq = FREQ_CACHE.get(c, 0)
                        ranked.append((c, freq))
                    
                    # Sort descending by frequency
                    ranked.sort(key=lambda x: x[1], reverse=True)
                    winner = ranked[0][0]
                    
                    if word.startswith('I') or word[0].isupper():
                        winner = winner.capitalize()
                        
                    # Low confidence warning for contextual particles/pronouns
                    low_confidence_words = ['ĉi', 'ĝi', 'ŝi', 'li', 'ni', 'vi', 'ili', 'ĝin', 'ŝin', 'lin', 'nin', 'vin', 'ilin', 'ĉiu', 'tiu', 'kiu', 'iu', 'neniu', 'ĉia', 'tia', 'kia', 'ia', 'nenia']
                    confidence = 0.60 if winner.lower() in low_confidence_words else 0.85
                    
                    return winner, confidence, "FREQUENCY_RECOVERY", hunspell_candidates
                else:
                    return None, 0.0, "NO_VALID_CANDIDATE", []
            else:
                if len(valid_candidates) > 1:
                    # Falback to Frequency if Hunspell is disabled
                    ranked = []
                    for c in valid_candidates:
                        freq = FREQ_CACHE.get(c, 0)
                        ranked.append((c, freq))
                    ranked.sort(key=lambda x: x[1], reverse=True)
                    winner = ranked[0][0]
                    if word.startswith('I') or word[0].isupper():
                        winner = winner.capitalize()
                    low_confidence_words = ['ĉi', 'ĝi', 'ŝi', 'li', 'ni', 'vi', 'ili', 'ĝin', 'ŝin', 'lin', 'nin', 'vin', 'ilin', 'ĉiu', 'tiu', 'kiu', 'iu', 'neniu']
                    confidence = 0.60 if winner.lower() in low_confidence_words else 0.85
                    return winner, confidence, "FREQUENCY_RECOVERY", valid_candidates
                else:
                    return None, 0.0, "NO_VALID_CANDIDATE", []

    # 5. Similarity
    if len(word) > 3 and all(ord(c) < 128 for c in word):
        matches = difflib.get_close_matches(lower_word, BASIC_ESPERANTO_DICT, n=1, cutoff=0.85)
        if matches:
            suggestion = matches[0]
            if any(c in suggestion for c in 'ĉĝĥĵŝŭ'):
                if word[0].isupper():
                    suggestion = suggestion.capitalize()
                return suggestion, 0.70, "Similitud", []
                
    return None, 0.0, None, []

def analyze_text_quality(filepath: str) -> dict:
    logger.info(f"Auditing text quality for {filepath}")
    doc = fitz.open(filepath)
    text_content = ""
    page_count = len(doc)
    for page in doc:
        text_content += page.get_text()
        
    # Normalizar Unicode a NFC
    text_content = unicodedata.normalize('NFC', text_content)
    
    # Classification counters
    total_chars = 0
    ascii_letters = 0
    unicode_letters = 0
    spaces = 0
    newlines = 0
    punctuation = 0
    esperanto_count = 0
    damaged_count = 0
    esperanto_chars = set(["ĉ", "ĝ", "ĥ", "ĵ", "ŝ", "ŭ", "Ĉ", "Ĝ", "Ĥ", "Ĵ", "Ŝ", "Ŭ"])
    damaged_markers = set(["■", "\ufffd", "\x00"]) 
    
    damaged_instances_detailed = []
    esperanto_audit_map = {c: {"count": 0, "pages": set()} for c in esperanto_chars}
    
    spanish_chars = ["á", "é", "í", "ó", "ú", "ñ", "Á", "É", "Í", "Ó", "Ú", "Ñ", "¿", "¡"]
    spanish_audit_map = {c: {"count": 0, "pages": set()} for c in spanish_chars}
    
    total_ascii = 0
    total_no_ascii = 0
    first_50_no_ascii = []
    
    from collections import Counter
    char_counter = Counter()
    word_page_map = {}

    for page_num, page in enumerate(doc):
        # Normalizar Unicode a NFC
        page_text = unicodedata.normalize('NFC', page.get_text())
        text_content += page_text
        
        # Use finditer to get exact match positions for snippet extraction
        # Include letters, damages chars, and our 'I' variant natively
        page_words = re.finditer(r'[A-Za-z■\ufffd]+', page_text)
        for m in page_words:
            w = m.group()
            if len(w) > 1:
                # Normalize \ufffd to ■ so they group together
                norm_w = w.replace("\ufffd", "■")
                if norm_w not in word_page_map:
                    # Extract ~30 chars around the word for context snippet
                    start_idx = max(0, m.start() - 30)
                    end_idx = min(len(page_text), m.end() + 30)
                    snippet = page_text[start_idx:end_idx].replace('\n', ' ').strip()
                    word_page_map[norm_w] = {"count": 0, "pages": set(), "snippet": snippet}
                word_page_map[norm_w]["count"] += 1
                word_page_map[norm_w]["pages"].add(page_num + 1)
        
        for c in page_text:
            char_counter[c] += 1
            if c in esperanto_chars:
                esperanto_audit_map[c]["count"] += 1
                esperanto_audit_map[c]["pages"].add(page_num + 1)
            if c in spanish_chars:
                spanish_audit_map[c]["count"] += 1
                spanish_audit_map[c]["pages"].add(page_num + 1)

    total_chars = len(text_content)
    
    for c in text_content:
        # Categorize
        if c in esperanto_chars:
            esperanto_count += 1
            unicode_letters += 1
        elif c in damaged_markers:
            damaged_count += 1
            if len(damaged_instances_detailed) < 50:
                damaged_instances_detailed.append({
                    "char": c,
                    "ord": ord(c),
                    "reason": "Marcador de daño conocido"
                })
        elif c.isspace():
            if c in ['\n', '\r']:
                newlines += 1
            else:
                spaces += 1
        elif c in string.ascii_letters:
            ascii_letters += 1
        elif c in string.punctuation:
            punctuation += 1
        elif c.isalpha():
            unicode_letters += 1
        elif unicodedata.category(c).startswith('P'):
            punctuation += 1
        elif unicodedata.category(c) == 'Co': # Uso privado, comúnmente fuentes sin mapeo
            damaged_count += 1
            if len(damaged_instances_detailed) < 50:
                damaged_instances_detailed.append({
                    "char": repr(c),
                    "ord": ord(c),
                    "reason": "Carácter de uso privado (Co) - Fuente sin mapeo"
                })
                
        # Estricto ASCII vs No-ASCII
        if ord(c) <= 127:
            total_ascii += 1
        else:
            total_no_ascii += 1
            if len(first_50_no_ascii) < 50:
                try:
                    uname = unicodedata.name(c)
                except ValueError:
                    uname = "UNKNOWN"
                first_50_no_ascii.append({
                    "char": repr(c) if c.isspace() or unicodedata.category(c) == 'Co' else c,
                    "ord": ord(c),
                    "hex": f"U+{ord(c):04X}",
                    "name": uname
                })
                
    # Detección y análisis de posibles palabras Esperanto perdidas
    missing_esperanto_analysis = []
    
    for word, data in word_page_map.items():
        suggestion, confidence, detection_type, amb_candidates = suggest_esperanto_correction(word)
        if suggestion or detection_type in ["UNRESOLVED_CORRUPTION", "AMBIGUOUS_CANDIDATES", "NO_VALID_CANDIDATE", "HUNSPELL_AMBIGUOUS_CANDIDATES"]:
            unicode_breakdown = ", ".join([f"{c} (U+{ord(c):04X})" for c in suggestion if ord(c) > 127]) if suggestion else ""
            missing_esperanto_analysis.append({
                "word": word,
                "suggestion": suggestion,
                "unicode_breakdown": unicode_breakdown,
                "detection_type": detection_type,
                "confidence": confidence,
                "count": data["count"],
                "ambiguous_candidates": amb_candidates,
                "pages": sorted(list(data["pages"])),
                "snippet": data["snippet"]
            })
            
    missing_esperanto_analysis.sort(key=lambda x: x["count"], reverse=True)
    
    # === GENERATE REPAIR PREVIEW ===
    repair_preview = {
        "total_corrections": 0,
        "by_type": {"X-System": 0, "Diccionario": 0, "Similitud": 0},
        "paragraphs": []
    }
    
    replacement_dict = {}
    for item in missing_esperanto_analysis:
        repair_preview["total_corrections"] += item["count"]
        rtype = item["detection_type"]
        repair_preview["by_type"][rtype] = repair_preview["by_type"].get(rtype, 0) + item["count"]
        replacement_dict[item["word"]] = item["suggestion"]
        
    lines = text_content.split('\n')
    preview_count = 0
    for line in lines:
        if len(line.strip()) < 15:
            continue
        
        has_correction = False
        def replace_match(m):
            w = m.group(0)
            if w in replacement_dict:
                return replacement_dict[w]
            return w
            
        corrected_line = re.sub(r'\b[A-Za-z]+\b', replace_match, line)
        if corrected_line != line:
            repair_preview["paragraphs"].append({
                "original": line.strip(),
                "corrected": corrected_line.strip()
            })
            preview_count += 1
            if preview_count >= 15: # Limit to 15 examples
                break
    
    # X-system (mantenemos el contador general por retrocompatibilidad)
    x_system_words = [item["word"] for item in missing_esperanto_analysis if item["confidence"] >= 0.9]
    x_system_count = sum(item["count"] for item in missing_esperanto_analysis if item["confidence"] >= 0.9)
    
    total_words = len(re.findall(r'\b\w+\b', text_content))
    
    snippets = []
    for m in re.finditer(r'.{0,40}[■\ufffd].{0,40}', text_content):
        snippets.append(m.group(0).replace('\n', ' '))
        if len(snippets) > 10: break
    
    doc.close()
    
    words = text_content.split()
    total_words = len(words)
    first_50_words = " ".join(words[:50])
    
    total_words_calc = total_words if total_words > 0 else 1
    
    error_ratio = (damaged_count + x_system_count) / total_words_calc
    text_validity_score = max(0.0, 100.0 - (error_ratio * 1000))
    unicode_score = 100.0 if damaged_count == 0 else max(0.0, 100.0 - (damaged_count * 2))
    overall_score = (unicode_score + text_validity_score) / 2
    
    logger.info(f"Text audit completed. Words: {total_words}, Special Chars: {esperanto_count}, Damaged: {damaged_count}")
    
    unicode_inventory = []
    for c, count in char_counter.most_common():
        if ord(c) > 127 or c in damaged_markers:
            try:
                uname = unicodedata.name(c)
            except ValueError:
                uname = "UNKNOWN OR PRIVATE USE"
                
            unicode_inventory.append({
                "char": repr(c) if c.isspace() or unicodedata.category(c) == 'Co' else c,
                "ord": ord(c),
                "hex": f"U+{ord(c):04X}",
                "name": uname,
                "count": count
            })
        
    formatted_esperanto_audit = []
    for c, data in esperanto_audit_map.items():
        formatted_esperanto_audit.append({
            "char": c,
            "count": data["count"],
            "pages": sorted(list(data["pages"]))
        })
        
    formatted_spanish_audit = []
    for c, data in spanish_audit_map.items():
        formatted_spanish_audit.append({
            "char": c,
            "count": data["count"],
            "pages": sorted(list(data["pages"]))
        })

    return {
        "damaged_chars_count": damaged_count,
        "esperanto_chars_count": esperanto_count,
        "x_system_count": x_system_count,
        "text_length": total_chars,
        "total_words": total_words,
        "first_50_words": first_50_words,
        "error_snippets": snippets + x_system_words[:5],
        "damaged_instances_detailed": damaged_instances_detailed,
        "unicode_inventory": unicode_inventory,
        "esperanto_audit": formatted_esperanto_audit,
        "spanish_audit": formatted_spanish_audit,
        "missing_esperanto_analysis": missing_esperanto_analysis[:100], # limit top 100
        "repair_preview": repair_preview,
        "unicode_debug": {
            "total_ascii": total_ascii,
            "total_no_ascii": total_no_ascii,
            "first_50_no_ascii": first_50_no_ascii
        },
        "classification": {
            "total": total_chars,
            "ascii_letters": ascii_letters,
            "unicode_letters": unicode_letters,
            "spaces": spaces,
            "newlines": newlines,
            "punctuation": punctuation,
            "esperanto_count": esperanto_count,
            "damaged_count": damaged_count
        },
        "valid_chars_count": total_chars - damaged_count,
        "unicode_score": round(unicode_score, 2),
        "text_validity_score": round(text_validity_score, 2),
        "overall_score": round(overall_score, 2),
        "page_count": page_count
    }
