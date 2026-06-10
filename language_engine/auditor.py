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
HUNSPELL_ES = None
try:
    HUNSPELL_DICT = Dictionary.from_files(os.path.join(os.path.dirname(__file__), "..", "data", "hunspell", "eo"))
    HUNSPELL_ES = Dictionary.from_files(os.path.join(os.path.dirname(__file__), "..", "data", "hunspell", "es_ES"))
except Exception as e:
    logger.warning(f"Failed to load Hunspell dictionary: {e}. 'Morfo' layer will be limited.")

FREQ_CACHE = {}
try:
    freq_path = os.path.join(os.path.dirname(__file__), "..", "data", "frequency_cache.json")
    if os.path.exists(freq_path):
        with open(freq_path, "r", encoding="utf-8") as f:
            FREQ_CACHE = json.load(f)
except Exception as e:
    logger.warning(f"Failed to load frequency cache (Frekvenco): {e}")

KUNTEKSTO_BIGRAMS = {}
KUNTEKSTO_TRIGRAMS = {}
try:
    context_path = os.path.join(os.path.dirname(__file__), "..", "data", "context_frequency.json")
    if os.path.exists(context_path):
        with open(context_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)
            KUNTEKSTO_BIGRAMS = dataset.get("bigrams", {})
            KUNTEKSTO_TRIGRAMS = dataset.get("trigrams", {})
except Exception as e:
    logger.warning(f"Failed to load context dataset (Kunteksto): {e}")

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

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
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

def suggest_esperanto_correction(word: str, snippet: str = "") -> dict:
    from language_engine.semantikisto import evaluate_candidate
    from language_engine.lingvo_detektilo import detect_language
    from language_engine.x_sistemo import normalize_x_system
    
    # 1. Normalize X-system
    normalized_word = normalize_x_system(word)
    if normalized_word != word:
        # If it was an X-system word, and now it's valid unicode Esperanto
        # we can just return it as a high confidence repair
        if Dictionary.from_files('data/hunspell/eo').lookup(normalized_word):
            return {"suggestion": normalized_word, "confidence": 0.99, "type": "SUCCESSFUL_REPAIR", "candidates": [normalized_word]}
            
    # 2. LingvoDetektilo pre-check
    # Prevent repairing valid Spanish or Proper names that OCR mangled slightly
    lang_scores = detect_language(word, snippet)
    is_explicitly_damaged = "I" in word or "■" in word
    
    if not is_explicitly_damaged:
        if lang_scores["spanish_score"] > 0.8:
            return {"suggestion": None, "confidence": 0.0, "type": "NO_VALID_CANDIDATE", "candidates": []}
        if lang_scores["proper_name_score"] > 0.8:
            return {"suggestion": None, "confidence": 0.0, "type": "NO_VALID_CANDIDATE", "candidates": []}
    
    try:
        lower_word = word.lower()
        if HUNSPELL_ES and HUNSPELL_ES.lookup(lower_word) and not is_explicitly_damaged:
            return {"suggestion": None, "confidence": 0.0, "type": "NO_VALID_CANDIDATE", "candidates": []}
            
        cands = list(HUNSPELL_DICT.suggest(word)) if HUNSPELL_DICT else []
        if not cands:
            return {"suggestion": None, "confidence": 0.0, "type": "NO_VALID_CANDIDATE", "candidates": []}
            
        # 3. Semantikisto Evaluation
        best_cand = None
        best_score = -1.0
        
        for cand in cands:
            score = evaluate_candidate(word, cand, snippet)
            if score > best_score:
                best_score = score
                best_cand = cand
                
        if best_cand and best_score >= 0.85:
            return {"suggestion": best_cand, "confidence": best_score, "type": "SUCCESSFUL_REPAIR", "candidates": cands}
        elif best_cand:
            return {"suggestion": best_cand, "confidence": best_score, "type": "AMBIGUOUS_CANDIDATES", "candidates": cands}
        else:
            return {"suggestion": cands[0], "confidence": 0.5, "type": "HUNSPELL_AMBIGUOUS_CANDIDATES", "candidates": cands}
            
    except Exception as e:
        logger.error(f"Error suggesting correction for {word}: {e}")
        return {"suggestion": None, "confidence": 0.0, "type": "ERROR", "candidates": []}

def legacy_suggest_esperanto_correction(word, snippet=""):
    damaged_markers = ['■', '\ufffd']
    if is_valid_esperanto(word) and not any(c in word for c in damaged_markers):
        return None, 0.0, "VALID", []
        
    if HUNSPELL_ES and HUNSPELL_ES.lookup(word) and not any(c in word for c in damaged_markers):
        return None, 0.0, "VALID_SPANISH", []

    # 0. Damaged Character Recovery (X-System like or hardcoded damaged rules)
    lower_word = word.lower()
    normalized_word = word.replace("\ufffd", "■")
    lower_normalized = normalized_word.lower()
    if "■" in lower_normalized:
        damaged_rules = {"e■": "eĉ", "■i": "ŝi", "■iu": "ĉiu", "■ar": "ĉar"}
        if lower_normalized in damaged_rules:
            suggestion = damaged_rules[lower_normalized]
            if word[0].isupper(): suggestion = suggestion.capitalize()
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
        if not is_valid_esperanto(suggestion):
            if HUNSPELL_DICT and not HUNSPELL_DICT.lookup(suggestion):
                confidence = 0.60
        return suggestion, confidence, "X-System", []

    # 2. Radiko: Glyph Corruption Recovery (Dictionary exact match)
    if lower_word in DICT_MAP:
        suggestion = DICT_MAP[lower_word]
        if word[0].isupper(): suggestion = suggestion.capitalize()
        return suggestion, 0.90, "Radiko", []

    # 3. Morphological & Hunspell Recovery (Morfo)
    target_candidates = []
    
    if "I" in word and word != "Iam":
        if bool(re.search(r'[a-z]I', word)) or (word.startswith("I") and len(word) > 1 and word[1:].islower()):
            candidates = generate_candidates(word)
            valid_candidates = []
            for cand in candidates:
                if is_valid_esperanto(cand):
                    valid_candidates.append(cand)
                    
            hunspell_candidates = []
            if HUNSPELL_DICT:
                for cand in candidates:
                    if HUNSPELL_DICT.lookup(cand):
                        hunspell_candidates.append(cand)
            
            target_candidates = hunspell_candidates if len(hunspell_candidates) > 0 else valid_candidates
    elif len(word) > 3 and all(ord(c) < 128 for c in word) and not is_valid_esperanto(word):
        possible_missing = [word + "ŭ", word + "n", "ĉ" + word[1:], "ĝ" + word[1:], "ĥ" + word[1:], "ĵ" + word[1:], "ŝ" + word[1:]]
        valid_missing = []
        for cand in possible_missing:
            if is_valid_esperanto(cand) or (HUNSPELL_DICT and HUNSPELL_DICT.lookup(cand)):
                valid_missing.append(cand)
        if valid_missing:
            target_candidates = valid_missing

    if len(target_candidates) == 1:
        suggestion = target_candidates[0]
        if word.startswith('I') or word[0].isupper(): suggestion = suggestion.capitalize()
        return suggestion, 0.95, "Morfo", []
    elif len(target_candidates) > 1:
        # We have multiple candidates. Time for Jugxanto!
                
        # Extract context from snippet, preserving markers
        snippet_tokens = re.sub(r'[^\w\^■]', ' ', snippet.lower()).split()
        prev2, prev_w, next_w, next2 = None, None, None, None
                
        try:
            # Find our broken word index in snippet (normalized)
            norm_word = lower_word.replace("\ufffd", "■")
            idx = -1
            for i, t in enumerate(snippet_tokens):
                if norm_word in t or t in norm_word:
                    idx = i
                    break
            if idx != -1:
                if idx > 0: prev_w = snippet_tokens[idx-1]
                if idx > 1: prev2 = snippet_tokens[idx-2]
                if idx < len(snippet_tokens)-1: next_w = snippet_tokens[idx+1]
                if idx < len(snippet_tokens)-2: next2 = snippet_tokens[idx+2]
                # Debug context
                if "i" in norm_word:
                    print(f"DEBUG: word='{norm_word}', snippet='{snippet}', prev='{prev_w}', next='{next_w}'")
        except Exception:
            pass

        def apply_gramatiko_rules(c, p, n):
            if c == "ĉi" and (n in ["tiu", "tie", "tio", "ĉi", "ĉia", "ĉies"] or p in ["tiu", "tie", "tio"]): return 100000
            if c in ["ŝi", "ĝi", "li"] and n and (n.endswith("is") or n.endswith("as") or n.endswith("os") or n.endswith("us")): return 100000
            if c == "ĝi" and n in ["estas", "havas", "povas"]: return 100000
            if c in ["ŝin", "ĝin", "lin"] and p and (p.endswith("is") or p.endswith("as") or p.endswith("os") or p.endswith("us") or p.endswith("i")): return 100000
            return 0

        def apply_gramatiko_bilingual(c, p2, p, n, n2):
            def check(words):
                for idx, w in enumerate([p, n, p2, n2]):
                    if w and w in words: return 100000000 / (10 ** idx)
                return 0
            if c == "li": return check({"él", "el", "yo"})
            if c == "ŝi": return check({"ella", "ellas"})
            if c == "ĝi": return check({"ello", "eso"})
            if c == "ĉi": return check({"este", "esta", "aquí", "esto"})
            if c.endswith("n"): return check({"al", "a"}) // 2
            return 0

        def apply_gramatiko_vocab(c, snippet_words):
            def is_es_inf(w): return w and len(w)>3 and w[-2:] in ["ar", "er", "ir"]
            if c.endswith(("i", "as", "is", "os", "us", "u", "a", "o")):
                for w in snippet_words:
                    if is_es_inf(w): return 100000
                    
            bilingual_nouns = {"plaĝo": "playa"}
            if c in bilingual_nouns:
                if bilingual_nouns[c] in snippet_words:
                    return 100000
                        
            if c in BASIC_ESPERANTO_DICT: return 10000
            return 0

        from .biblioteko import biblioteko
        
        jugxanto_scores = []
        for c in target_candidates:
            c_lower = c.lower()
                    
            # Frekvenco: Biblioteko Unigram Frequency
            frekvenco_score = biblioteko.get_word_frequency(c_lower)
            # Legacy fallback
            if frekvenco_score == 0: frekvenco_score = FREQ_CACHE.get(c_lower, 0)
                    
            # Kunteksto: Biblioteko Co-occurrences
            kunteksto_score = 0
            if snippet_tokens:
                for cw in snippet_tokens:
                    if cw != c_lower:
                        kunteksto_score += biblioteko.get_co_occurrence(c_lower, cw)
            
            # Legacy Bigrams/Trigrams fallback
            if kunteksto_score == 0:
                if prev_w: kunteksto_score += KUNTEKSTO_BIGRAMS.get(f"{prev_w} {c_lower}", 0)
                if next_w: kunteksto_score += KUNTEKSTO_BIGRAMS.get(f"{c_lower} {next_w}", 0)
                if prev_w and next_w: kunteksto_score += KUNTEKSTO_TRIGRAMS.get(f"{prev_w} {c_lower} {next_w}", 0) * 2
                
            # Memoro (Historical evidence)
            memory_confidence = biblioteko.get_historical_confidence(lower_word, c_lower)
            
            # Gramatiko
            g_rules = apply_gramatiko_rules(c_lower, prev_w, next_w)
            g_bilingual = apply_gramatiko_bilingual(c_lower, prev2, prev_w, next_w, next2)
            g_vocab = apply_gramatiko_vocab(c_lower, snippet_tokens)
            
            # Memoro adds a massive boost if historical confidence is > 0.85
            memory_bonus = 1000000 if memory_confidence >= 0.85 else 0
            
            total_score = frekvenco_score + (kunteksto_score * 5) + g_rules + g_bilingual + g_vocab + memory_bonus
            jugxanto_scores.append((c, total_score, frekvenco_score, kunteksto_score, g_rules, g_bilingual, g_vocab, memory_bonus))
                
        jugxanto_scores.sort(key=lambda x: x[1], reverse=True)
        winner, t_score, f_score, k_score, gr_score, gb_score, gv_score, mem_score = jugxanto_scores[0]
                
        if word.startswith('I') or word[0].isupper():
            winner = winner.capitalize()

        # Calculate confidence to avoid bad silent replacements
        second_score = jugxanto_scores[1][1] if len(jugxanto_scores) > 1 else 0
        total_t = t_score + second_score
                
        confidence = 0.85
        layer_used = "Frekvenco"
                
        if mem_score > 0:
            confidence = 0.99
            layer_used = "Memoro"
        elif gb_score > 0:
            confidence = 0.95
            layer_used = "Gramatiko_Bilingual"
        elif gv_score > 0:
            confidence = 0.95
            layer_used = "Gramatiko_Vocab"
        elif gr_score > 0:
            confidence = 0.95
            layer_used = "Gramatiko"
        elif total_t == 0:
            confidence = 0.60
            layer_used = "Jugxanto_ManualReview"
        elif t_score / total_t < 0.85:
            confidence = 0.60
            layer_used = "Jugxanto_ManualReview"
        else:
            if k_score > 0: layer_used = "Kunteksto"
            else: layer_used = "Frekvenco"
                
        detailed_cands = [
            {
                "candidate": s[0], "total_score": s[1], "frekvenco_freq": s[2],
                "kunteksto_context": s[3], "gramatiko_rules": s[4] + s[5] + s[6],
                "memoro_score": s[7]
            } for s in jugxanto_scores
        ]
        return winner, confidence, layer_used, detailed_cands
    else:
        pass # Fall through to legacy similarity

    # 5. Similarity (Legacy)
    if len(word) > 3 and all(ord(c) < 128 for c in word):
        matches = difflib.get_close_matches(lower_word, BASIC_ESPERANTO_DICT, n=1, cutoff=0.85)
        if matches:
            suggestion = matches[0]
            if any(c in suggestion for c in 'ĉĝĥĵŝŭ'):
                if word[0].isupper(): suggestion = suggestion.capitalize()
                return suggestion, 0.70, "Similitud", []
                
    if not any(c in word for c in damaged_markers):
        return None, 0.0, "UNRECOGNIZED_WORD", []
        
    return None, 0.0, "NO_VALID_CANDIDATE", []
from collections import Counter

def _populate_maps(page_text, page_num_1_indexed, word_page_map, char_counter, esperanto_audit_map, spanish_audit_map):
    esperanto_chars = set(["ĉ", "ĝ", "ĥ", "ĵ", "ŝ", "ŭ", "Ĉ", "Ĝ", "Ĥ", "Ĵ", "Ŝ", "Ŭ"])
    spanish_chars = ["á", "é", "í", "ó", "ú", "ñ", "Á", "É", "Í", "Ó", "Ú", "Ñ", "¿", "¡"]
    
    page_words = re.finditer(r'[A-Za-z■�]+', page_text)
    for m in page_words:
        w = m.group()
        if len(w) > 1:
            norm_w = w.replace("\ufffd", "■")
            if norm_w not in word_page_map:
                start_idx = max(0, m.start() - 30)
                end_idx = min(len(page_text), m.end() + 30)
                snippet = page_text[start_idx:end_idx].replace('\n', ' ').strip()
                word_page_map[norm_w] = {"count": 0, "pages": set(), "snippet": snippet}
            word_page_map[norm_w]["count"] += 1
            word_page_map[norm_w]["pages"].add(page_num_1_indexed)
    
    for c in page_text:
        char_counter[c] += 1
        if c in esperanto_chars:
            esperanto_audit_map[c]["count"] += 1
            esperanto_audit_map[c]["pages"].add(page_num_1_indexed)
        if c in spanish_chars:
            spanish_audit_map[c]["count"] += 1
            spanish_audit_map[c]["pages"].add(page_num_1_indexed)

def analyze_raw_text(text_content: str) -> dict:
    logger.info("Auditing raw text (TXT/Clipboard)")
    text_content = unicodedata.normalize('NFC', text_content)
    char_counter = Counter()
    word_page_map = {}
    esperanto_chars = set(["ĉ", "ĝ", "ĥ", "ĵ", "ŝ", "ŭ", "Ĉ", "Ĝ", "Ĥ", "Ĵ", "Ŝ", "Ŭ"])
    spanish_chars = ["á", "é", "í", "ó", "ú", "ñ", "Á", "É", "Í", "Ó", "Ú", "Ñ", "¿", "¡"]
    esperanto_audit_map = {c: {"count": 0, "pages": set()} for c in esperanto_chars}
    spanish_audit_map = {c: {"count": 0, "pages": set()} for c in spanish_chars}

    _populate_maps(text_content, 1, word_page_map, char_counter, esperanto_audit_map, spanish_audit_map)
    return _analyze_extracted_data(text_content, word_page_map, char_counter, esperanto_audit_map, spanish_audit_map, 1)

def analyze_text_quality(filepath: str) -> dict:
    logger.info(f"Auditing text quality for {filepath}")
    doc = fitz.open(filepath)
    text_content = ""
    page_count = len(doc)
    
    char_counter = Counter()
    word_page_map = {}
    esperanto_chars = set(["ĉ", "ĝ", "ĥ", "ĵ", "ŝ", "ŭ", "Ĉ", "Ĝ", "Ĥ", "Ĵ", "Ŝ", "Ŭ"])
    spanish_chars = ["á", "é", "í", "ó", "ú", "ñ", "Á", "É", "Í", "Ó", "Ú", "Ñ", "¿", "¡"]
    esperanto_audit_map = {c: {"count": 0, "pages": set()} for c in esperanto_chars}
    spanish_audit_map = {c: {"count": 0, "pages": set()} for c in spanish_chars}

    for page_num, page in enumerate(doc):
        page_text = unicodedata.normalize('NFC', page.get_text())
        text_content += page_text
        _populate_maps(page_text, page_num + 1, word_page_map, char_counter, esperanto_audit_map, spanish_audit_map)
        
    doc.close()
    return _analyze_extracted_data(text_content, word_page_map, char_counter, esperanto_audit_map, spanish_audit_map, page_count)

def _analyze_extracted_data(text_content, word_page_map, char_counter, esperanto_audit_map, spanish_audit_map, page_count):
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
    
    total_ascii = 0
    total_no_ascii = 0
    first_50_no_ascii = []
    
    total_chars = len(text_content)
    
    for c in text_content:
        if c in esperanto_chars:
            esperanto_count += 1
            unicode_letters += 1
        elif c in damaged_markers:
            damaged_count += 1
            if len(damaged_instances_detailed) < 50:
                damaged_instances_detailed.append({"char": c, "ord": ord(c), "reason": "Marcador de daño conocido"})
        elif c.isspace():
            if c in ['\n', '\r']: newlines += 1
            else: spaces += 1
        elif c in string.ascii_letters:
            ascii_letters += 1
        elif c in string.punctuation:
            punctuation += 1
        elif c.isalpha():
            unicode_letters += 1
        elif unicodedata.category(c).startswith('P'):
            punctuation += 1
        elif unicodedata.category(c) == 'Co':
            damaged_count += 1
            if len(damaged_instances_detailed) < 50:
                damaged_instances_detailed.append({"char": repr(c), "ord": ord(c), "reason": "Uso privado"})
                
        if ord(c) <= 127: total_ascii += 1
        else:
            total_no_ascii += 1
            if len(first_50_no_ascii) < 50:
                try: uname = unicodedata.name(c)
                except ValueError: uname = "UNKNOWN"
                first_50_no_ascii.append({"char": repr(c) if c.isspace() or unicodedata.category(c) == 'Co' else c, "ord": ord(c), "hex": f"U+{ord(c):04X}", "name": uname})
                
    missing_esperanto_analysis = []
    arkitekturo_metrics = {"radiko_resolved": 0, "morfo_resolved": 0, "frekvenco_resolved": 0, "kunteksto_resolved": 0, "gramatiko_resolved": 0, "bilingual_resolved": 0, "vocabulary_table_resolved": 0, "jugxanto_resolved": 0, "unresolved_after_jugxanto": 0, "unresolved_after_bilingual": 0}
    
    for word, data in word_page_map.items():
        suggestion, confidence, detection_type, amb_candidates = suggest_esperanto_correction(word, snippet=data["snippet"])
        if suggestion or detection_type in ["UNRESOLVED_CORRUPTION", "AMBIGUOUS_CANDIDATES", "NO_VALID_CANDIDATE", "HUNSPELL_AMBIGUOUS_CANDIDATES", "Jugxanto_ManualReview"]:
            if detection_type == "Radiko": arkitekturo_metrics["radiko_resolved"] += data["count"]
            elif detection_type == "Morfo": arkitekturo_metrics["morfo_resolved"] += data["count"]
            elif detection_type == "Frekvenco": arkitekturo_metrics["frekvenco_resolved"] += data["count"]
            elif detection_type == "Kunteksto": arkitekturo_metrics["kunteksto_resolved"] += data["count"]
            elif detection_type == "Gramatiko": arkitekturo_metrics["gramatiko_resolved"] += data["count"]
            elif detection_type == "Gramatiko_Bilingual": arkitekturo_metrics["bilingual_resolved"] += data["count"]
            elif detection_type == "Gramatiko_Vocab": arkitekturo_metrics["vocabulary_table_resolved"] += data["count"]
            elif detection_type == "Jugxanto_ManualReview": 
                arkitekturo_metrics["unresolved_after_jugxanto"] += data["count"]
                arkitekturo_metrics["unresolved_after_bilingual"] += data["count"]
            
            if detection_type in ["Frekvenco", "Kunteksto", "Gramatiko", "Gramatiko_Bilingual", "Gramatiko_Vocab"]:
                arkitekturo_metrics["jugxanto_resolved"] += data["count"]

            unicode_breakdown = ", ".join([f"{c} (U+{ord(c):04X})" for c in suggestion if ord(c) > 127]) if suggestion else ""
            missing_esperanto_analysis.append({
                "word": word, "suggestion": suggestion, "unicode_breakdown": unicode_breakdown,
                "detection_type": detection_type, "confidence": confidence, "count": data["count"],
                "ambiguous_candidates": amb_candidates, "pages": sorted(list(data["pages"])), "snippet": data["snippet"]
            })
            
    missing_esperanto_analysis.sort(key=lambda x: x["count"], reverse=True)
    
    repair_preview = {"total_corrections": 0, "by_type": {"X-System": 0, "Diccionario": 0, "Similitud": 0}, "paragraphs": []}
    replacement_dict = {}
    for item in missing_esperanto_analysis:
        repair_preview["total_corrections"] += item["count"]
        rtype = item["detection_type"]
        repair_preview["by_type"][rtype] = repair_preview["by_type"].get(rtype, 0) + item["count"]
        replacement_dict[item["word"]] = item["suggestion"]
        
    lines = text_content.split('\n')
    preview_count = 0
    for line in lines:
        if len(line.strip()) < 15: continue
        def replace_match(m):
            w = m.group(0)
            if w in replacement_dict: return replacement_dict[w]
            return w
        corrected_line = re.sub(r'\b[A-Za-z]+\b', replace_match, line)
        if corrected_line != line:
            repair_preview["paragraphs"].append({"original": line.strip(), "corrected": corrected_line.strip()})
            preview_count += 1
            if preview_count >= 15: break
    
    x_system_words = [item["word"] for item in missing_esperanto_analysis if item["confidence"] >= 0.9]
    x_system_count = sum(item["count"] for item in missing_esperanto_analysis if item["confidence"] >= 0.9)
    
    total_words = len(re.findall(r'\b\w+\b', text_content))
    snippets = []
    for m in re.finditer(r'.{0,40}[■\ufffd].{0,40}', text_content):
        snippets.append(m.group(0).replace('\n', ' '))
        if len(snippets) > 10: break
    
    words = text_content.split()
    total_words = len(words)
    first_50_words = " ".join(words[:50])
    
    total_words_calc = total_words if total_words > 0 else 1
    error_ratio = (damaged_count + x_system_count) / total_words_calc
    text_validity_score = max(0.0, 100.0 - (error_ratio * 1000))
    unicode_score = 100.0 if damaged_count == 0 else max(0.0, 100.0 - (damaged_count * 2))
    overall_score = (unicode_score + text_validity_score) / 2
    
    logger.info(f"Text audit completed. Words: {total_words}, Damaged: {damaged_count}")
    
    unicode_inventory = []
    for c, count in char_counter.most_common():
        if ord(c) > 127 or c in damaged_markers:
            try: uname = unicodedata.name(c)
            except ValueError: uname = "UNKNOWN OR PRIVATE USE"
            unicode_inventory.append({"char": repr(c) if c.isspace() or unicodedata.category(c) == 'Co' else c, "ord": ord(c), "hex": f"U+{ord(c):04X}", "name": uname, "count": count})
        
    formatted_esperanto_audit = []
    for c, data in esperanto_audit_map.items():
        formatted_esperanto_audit.append({"char": c, "count": data["count"], "pages": sorted(list(data["pages"]))})
        
    formatted_spanish_audit = []
    for c, data in spanish_audit_map.items():
        formatted_spanish_audit.append({"char": c, "count": data["count"], "pages": sorted(list(data["pages"]))})

    return {
        "damaged_chars_count": damaged_count, "esperanto_chars_count": esperanto_count, "x_system_count": x_system_count,
        "text_length": total_chars, "total_words": total_words, "first_50_words": first_50_words,
        "error_snippets": snippets + x_system_words[:5], "damaged_instances_detailed": damaged_instances_detailed,
        "unicode_inventory": unicode_inventory, "esperanto_audit": formatted_esperanto_audit, "spanish_audit": formatted_spanish_audit,
        "missing_esperanto_analysis": missing_esperanto_analysis, "repair_preview": repair_preview,
        "unicode_debug": {"total_ascii": total_ascii, "total_no_ascii": total_no_ascii, "first_50_no_ascii": first_50_no_ascii},
        "classification": {"total": total_chars, "ascii_letters": ascii_letters, "unicode_letters": unicode_letters, "spaces": spaces, "newlines": newlines, "punctuation": punctuation, "esperanto_count": esperanto_count, "damaged_count": damaged_count},
        "valid_chars_count": total_chars - damaged_count, "unicode_score": round(unicode_score, 2),
        "text_validity_score": round(text_validity_score, 2), "overall_score": round(overall_score, 2),
        "page_count": page_count, "arkitekturo_metrics": arkitekturo_metrics
    }
