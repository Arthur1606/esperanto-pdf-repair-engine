import glob
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.services.auditor import analyze_text_quality

files = sorted(glob.glob(os.path.join(os.path.dirname(__file__), '..', 'uploads', 'leccion_*.pdf')))

print("Extracting 21 MR cases...")
for f in files:
    try:
        res = analyze_text_quality(f)
        for item in res.get("missing_esperanto_analysis", []):
            if item["detection_type"] == "Triforce_ManualReview":
                for _ in range(item["count"]):
                    print(f"File: {os.path.basename(f)}")
                    print(f"Word: {item['word']} -> {item['ambiguous_candidates']}")
                    print(f"Snippet: {item['snippet']}")
                    print("-" * 50)
    except Exception as e:
        print(f"Error {f}: {e}")
