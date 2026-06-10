import glob
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from language_engine.auditor import analyze_text_quality

files = sorted(glob.glob(os.path.join(os.path.dirname(__file__), '..', '..', 'uploads', 'leccion_*.pdf')))

all_manual_reviews = []

print("Extracting Manual Review cases...")
for f in files:
    try:
        res = analyze_text_quality(f)
        for item in res.get("missing_esperanto_analysis", []):
            if item["confidence"] < 0.85 or item["detection_type"] == "Jugxanto_ManualReview":
                for _ in range(item["count"]):
                    all_manual_reviews.append({
                        "file": os.path.basename(f),
                        "word": item["word"],
                        "snippet": item["snippet"],
                        "candidates": item["ambiguous_candidates"]
                    })
    except Exception as e:
        pass

print(f"Total MRs found: {len(all_manual_reviews)}")

thresholds = [0.85, 0.80, 0.75, 0.70]
resolved_at = {0.85: 0, 0.80: 0, 0.75: 0, 0.70: 0}

for mr in all_manual_reviews:
    print(f"\n[{mr['file']}] Word: {mr['word']}")
    print(f"Snippet: {mr['snippet']}")
    cands = sorted(mr["candidates"], key=lambda x: x["total_score"], reverse=True)
    
    top1 = cands[0]
    top2 = cands[1] if len(cands) > 1 else {"total_score": 0}
    
    total_t = top1["total_score"] + top2["total_score"]
    ratio = top1["total_score"] / total_t if total_t > 0 else 0
    
    print(f"Top 1: {top1['candidate']} (Score: {top1['total_score']}, N: {top1['frekvenco_freq']}, O: {top1['kunteksto_context']}, F: {top1['gramatiko_rules']})")
    print(f"Top 2: {top2['candidate']} (Score: {top2['total_score']}, N: {top2['frekvenco_freq']}, O: {top2['kunteksto_context']}, F: {top2['gramatiko_rules']})")
    print(f"Ratio: {ratio:.4f}")
    
    for t in thresholds:
        if ratio >= t and total_t > 0:
            resolved_at[t] += 1

print("\n--- THRESHOLD SIMULATION ---")
for t in thresholds:
    print(f"Threshold {t}: {resolved_at[t]} cases would be resolved.")
