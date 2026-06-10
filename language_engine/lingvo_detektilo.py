import re

# Offline Spanish heuristics
SPANISH_SUFFIXES = ['ción', 'sión', 'dad', 'mente', 'ismo', 'ista', 'dor', 'dora', 'ura']
SPANISH_STOPWORDS = {'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'pero', 'que', 'de', 'en', 'a', 'con', 'por', 'para', 'sin', 'sobre'}

def detect_language(word: str, context: str = "") -> dict:
    """
    LingvoDetektilo: Identifies the likely language or nature of a word to prevent
    the repair engine from corrupting non-Esperanto terms.
    """
    scores = {
        "esperanto_score": 0.0,
        "spanish_score": 0.0,
        "proper_name_score": 0.0,
        "technical_term_score": 0.0
    }
    
    word_lower = word.lower()
    
    # 1. Proper Name Detection
    # If the word starts with a capital letter and isn't at the very start of a sentence
    # (a simple heuristic without full NLP), it's highly likely a proper name.
    # We also check if it's all uppercase (acronyms like SAT).
    if word.isupper() and len(word) > 1:
        scores["proper_name_score"] = 0.9
    elif word.istitle():
        # If context is available, check if the preceding word ends with a period.
        if context:
            parts = context.split()
            try:
                idx = parts.index(word)
                if idx > 0 and parts[idx-1].endswith('.'):
                    # Start of sentence
                    scores["proper_name_score"] = 0.3
                else:
                    scores["proper_name_score"] = 0.8
            except ValueError:
                scores["proper_name_score"] = 0.6
        else:
            scores["proper_name_score"] = 0.6
            
    # 2. Technical Term Detection
    # Has numbers, hyphens in weird places, or mixed casing (e.g., X-ray, iPhone, UTF-8)
    if re.search(r'\d', word) or '-' in word[1:-1]:
        scores["technical_term_score"] = 0.85
        
    # 3. Spanish Score
    if word_lower in SPANISH_STOPWORDS:
        scores["spanish_score"] = 0.95
    else:
        for suffix in SPANISH_SUFFIXES:
            if word_lower.endswith(suffix):
                scores["spanish_score"] += 0.5
                
        # If it has accents typical of Spanish but illegal in standard Esperanto
        if re.search(r'[áéíóúñÁÉÍÓÚÑ]', word):
            scores["spanish_score"] += 0.7

    # 4. Esperanto Score
    # Typical Esperanto endings (-o, -a, -e, -i, -is, -as, -os, -us, -u, -j, -n)
    if re.search(r'(o|a|e|i|is|as|os|us|u|j|n)$', word_lower):
        scores["esperanto_score"] += 0.4
    if re.search(r'[ĉĝĥĵŝŭĈĜĤĴŜŬ]', word):
        scores["esperanto_score"] += 0.6
        
    # Cap scores at 1.0
    for k in scores:
        scores[k] = min(1.0, scores[k])
        
    return scores
