import json
import os

base_dir = os.path.dirname(os.path.dirname(__file__))
context_path = os.path.join(base_dir, '..', 'data', 'context_frequency.json')
cache_path = os.path.join(base_dir, '..', 'data', 'frequency_cache.json')

print("Reading context_frequency.json...")
with open(context_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

bigrams = data.get('bigrams', {})

unigrams = {}
for bg, count in bigrams.items():
    w1, w2 = bg.split(' ')
    unigrams[w1] = unigrams.get(w1, 0) + count
    unigrams[w2] = unigrams.get(w2, 0) + count

print(f"Generated {len(unigrams)} unigrams.")

# Override with some hardcoded to be safe but the rest are pure math
with open(cache_path, 'r', encoding='utf-8') as f:
    old_cache = json.load(f)

for k, v in old_cache.items():
    if k not in unigrams:
        unigrams[k] = v

with open(cache_path, 'w', encoding='utf-8') as f:
    json.dump(unigrams, f, indent=2, ensure_ascii=False)

print("frequency_cache.json written successfully.")
