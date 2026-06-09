import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import glob
from app.services.auditor import analyze_text_quality
from app.core.database import SessionLocal
import json

print("| Palabra Original | Candidatos | Confianza (Simulada) | Contexto | Archivo |")
print("|---|---|---|---|---|")

for filepath in glob.glob("uploads/*.pdf"):
    try:
        debug_info = analyze_text_quality(filepath)
        filename = os.path.basename(filepath)
        for amb in debug_info.get("glyph_corruption_metrics", {}).get("ambiguity_catalogue", []):
            word = amb["word"]
            candidates = amb["candidates"]
            
            # Find context in debug_info paragraphs
            context = "Contexto no encontrado"
            for p in debug_info.get("paragraphs", []):
                original_text = p.get("original", "")
                words = original_text.split()
                # find the word or something similar
                for i, w in enumerate(words):
                    if len(w) > 1 and word in w:
                        start = max(0, i - 5)
                        end = min(len(words), i + 6)
                        context = " ".join(words[start:end])
                        break
            
            winner = candidates[0] if candidates else "N/A"
            print(f"| {word} | {', '.join(candidates)} | {winner} | 0.60 | {context} | {filename} |")
    except Exception as e:
        print(f"Error con {filepath}: {e}")
