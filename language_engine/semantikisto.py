import logging

from language_engine.biblioteko import biblioteko
from language_engine.lingvo_detektilo import detect_language
from language_engine.x_sistemo import normalize_x_system

logger = logging.getLogger(__name__)

def evaluate_candidate(original_word: str, candidate_word: str, context: str) -> float:
    """
    Semantikisto: The strategic director for ambiguous candidates.
    Coordinates evidence from Biblioteko, Memoro, Frekvenco, and Kunteksto
    to determine a final mathematically sound confidence score.
    """
    base_confidence = 0.50
    
    # Normalize X-system on the candidate just in case
    candidate_word = normalize_x_system(candidate_word)
    
    # 1. LingvoDetektilo check on original word
    # If the original word is highly likely Spanish or a Proper Noun,
    # we heavily penalize repairing it into an Esperanto word,
    # unless it also contains an explicit damage marker like "I" or "■".
    lang_scores = detect_language(original_word, context)
    is_explicitly_damaged = "I" in original_word or "■" in original_word
    
    if not is_explicitly_damaged:
        if lang_scores["spanish_score"] > 0.8:
            logger.debug(f"Semantikisto: {original_word} rejected. High Spanish score.")
            return 0.0
        if lang_scores["proper_name_score"] > 0.8:
            logger.debug(f"Semantikisto: {original_word} rejected. High Proper Name score.")
            return 0.0
        if lang_scores["technical_term_score"] > 0.8:
            logger.debug(f"Semantikisto: {original_word} rejected. High Technical Term score.")
            return 0.0
            
    # 2. Biblioteko / Frekvenco
    # Does the candidate exist in the massive corpus?
    freq = biblioteko.get_word_frequency(candidate_word)
    if freq > 0:
        base_confidence += 0.20
        # If it's a very common word in the literature
        if freq > 100:
            base_confidence += 0.05
            
    # 3. Kunteksto
    # Does the candidate co-occur with surrounding words?
    if context:
        parts = context.split()
        try:
            # Simple fallback context window analysis
            idx = parts.index(original_word)
            if idx > 0:
                prev_word = parts[idx-1].strip(".,!?:;()[]")
                co_occ = biblioteko.get_co_occurrence(prev_word, candidate_word, max_distance=1)
                if co_occ > 0:
                    base_confidence += 0.15
            if idx < len(parts) - 1:
                next_word = parts[idx+1].strip(".,!?:;()[]")
                co_occ = biblioteko.get_co_occurrence(candidate_word, next_word, max_distance=1)
                if co_occ > 0:
                    base_confidence += 0.15
        except ValueError:
            pass
            
    # 4. Memoro
    # Has this specific repair been successful before?
    memoro_bonus = biblioteko.get_historical_confidence(original_word, candidate_word)
    if memoro_bonus > 0:
        base_confidence += 0.30 # Massive boost from historical truth
        
    return min(1.0, base_confidence)
