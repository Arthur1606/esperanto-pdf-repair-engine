import re
import logging

logger = logging.getLogger(__name__)

X_SYSTEM_MAP = {
    'cx': 'ĉ', 'gx': 'ĝ', 'hx': 'ĥ', 'jx': 'ĵ', 'sx': 'ŝ', 'ux': 'ŭ',
    'Cx': 'Ĉ', 'Gx': 'Ĝ', 'Hx': 'Ĥ', 'Jx': 'Ĵ', 'Sx': 'Ŝ', 'Ux': 'Ŭ',
    'CX': 'Ĉ', 'GX': 'Ĝ', 'HX': 'Ĥ', 'JX': 'Ĵ', 'SX': 'Ŝ', 'UX': 'Ŭ'
}

def normalize_x_system(word: str) -> str:
    """
    Normalizes a single word from X-sistemo to standard Esperanto Unicode.
    """
    if 'x' not in word.lower():
        return word
        
    normalized = word
    for x_char, unicode_char in X_SYSTEM_MAP.items():
        normalized = normalized.replace(x_char, unicode_char)
    return normalized

def detect_and_normalize_document(text: str) -> str:
    """
    Analyzes a full text to determine if it heavily uses X-sistemo.
    If it detects intentional X-sistemo, it normalizes it.
    """
    # Quick heuristic: if we see 'cx', 'sx', 'gx' frequently
    x_matches = len(re.findall(r'[cghjsu]x', text, re.IGNORECASE))
    unicode_matches = len(re.findall(r'[ĉĝĥĵŝŭ]', text, re.IGNORECASE))
    
    # If X-system usage is significantly higher than Unicode usage, normalize
    if x_matches > 5 and x_matches > unicode_matches:
        logger.info(f"X-Sistemo Engine: Detected X-sistemo document ({x_matches} matches). Normalizing to Unicode.")
        normalized_text = text
        for x_char, unicode_char in X_SYSTEM_MAP.items():
            normalized_text = normalized_text.replace(x_char, unicode_char)
        return normalized_text
        
    return text
