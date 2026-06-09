import glob
import os
import json
import sys

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.auditor import analyze_text_quality

total_zelda_metrics = {
    "deku_resolved": 0,
    "sheikah_resolved": 0,
    "nayru_resolved": 0,
    "ocarina_resolved": 0,
    "farore_resolved": 0,
    "triforce_resolved": 0,
    "unresolved_after_triforce": 0
}

files = sorted(glob.glob(os.path.join(os.path.dirname(__file__), '..', 'uploads', 'leccion_*.pdf')))
print(f"Starting B2 Benchmark on {len(files)} PDFs...")

total_words = 0
total_damaged = 0

for filepath in files:
    try:
        res = analyze_text_quality(filepath)
        zm = res.get("zelda_metrics", {})
        for k in total_zelda_metrics:
            total_zelda_metrics[k] += zm.get(k, 0)
        total_words += res.get("total_words", 0)
        total_damaged += res.get("damaged_chars_count", 0)
        print(f"Processed {os.path.basename(filepath)} - Unresolved MRs: {zm.get('unresolved_after_triforce', 0)}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

print("\n--- ZELDA METRICS (FASE B2) ---")
for k, v in total_zelda_metrics.items():
    print(f"{k}: {v}")

total_ambiguous = total_zelda_metrics["triforce_resolved"] + total_zelda_metrics["unresolved_after_triforce"]
reduction = (total_zelda_metrics["triforce_resolved"] / total_ambiguous * 100) if total_ambiguous > 0 else 0

print(f"\nTotal Contextual Ambigüedades Tratadas por Triforce: {total_ambiguous}")
print(f"Resueltas por Contexto/Reglas (No Human): {total_zelda_metrics['triforce_resolved']}")
print(f"Caen a Manual Review (Unresolved): {total_zelda_metrics['unresolved_after_triforce']}")
print(f"REDUCCIÓN DE MANUAL REVIEW: {reduction:.2f}%")

with open("/tmp/b2_metrics.json", "w") as f:
    json.dump({
        "metrics": total_zelda_metrics,
        "reduction": reduction,
        "total_ambiguous": total_ambiguous
    }, f)
