import glob
import os
import json
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.auditor import analyze_text_quality

total_zelda_metrics = {
    "deku_resolved": 0,
    "sheikah_resolved": 0,
    "nayru_resolved": 0,
    "ocarina_resolved": 0,
    "farore_resolved": 0,
    "bilingual_resolved": 0,
    "vocabulary_table_resolved": 0,
    "triforce_resolved": 0,
    "unresolved_after_bilingual": 0
}

files = sorted(glob.glob(os.path.join(os.path.dirname(__file__), '..', 'uploads', 'leccion_*.pdf')))
print(f"Starting B4 Benchmark on {len(files)} PDFs...")

for filepath in files:
    try:
        res = analyze_text_quality(filepath)
        zm = res.get("zelda_metrics", {})
        for k in total_zelda_metrics:
            total_zelda_metrics[k] += zm.get(k, 0)
        print(f"Processed {os.path.basename(filepath)} - Unresolved MRs: {zm.get('unresolved_after_bilingual', 0)}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

print("\n--- ZELDA METRICS (FASE B4) ---")
for k, v in total_zelda_metrics.items():
    print(f"{k}: {v}")

total_ambiguous = total_zelda_metrics["triforce_resolved"] + total_zelda_metrics["unresolved_after_bilingual"]
reduction = (total_zelda_metrics["triforce_resolved"] / total_ambiguous * 100) if total_ambiguous > 0 else 0

print(f"\nTotal Contextual Ambigüedades Tratadas por Triforce: {total_ambiguous}")
print(f"Resueltas por Triforce (No Human): {total_zelda_metrics['triforce_resolved']}")
print(f"Bilingual Resolved: {total_zelda_metrics['bilingual_resolved']}")
print(f"Vocab Table Resolved: {total_zelda_metrics['vocabulary_table_resolved']}")
print(f"Caen a Manual Review (Unresolved): {total_zelda_metrics['unresolved_after_bilingual']}")
print(f"REDUCCIÓN DE MANUAL REVIEW: {reduction:.2f}%")
