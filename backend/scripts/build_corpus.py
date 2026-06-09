import urllib.request
import bz2
import json
import re
from collections import Counter
import os

url = "https://downloads.tatoeba.org/exports/per_language/epo/epo_sentences.tsv.bz2"
print(f"Downloading corpus from {url}...")
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
response = urllib.request.urlopen(req)
compressed_data = response.read()
print("Download complete. Decompressing...")

data = bz2.decompress(compressed_data).decode('utf-8')
sentences = []
for line in data.split('\n'):
    parts = line.split('\t')
    if len(parts) >= 3:
        sentences.append(parts[2].strip())

print(f"Total sentences extracted: {len(sentences)}")

# N-gram extraction
bigrams = Counter()
trigrams = Counter()
unique_vocab = set()

def tokenize(text):
    text = text.lower()
    text = re.sub(r'[^\w\^]', ' ', text)
    return text.split()

print("Processing n-grams...")
for sentence in sentences:
    words = tokenize(sentence)
    unique_vocab.update(words)
    for i in range(len(words) - 1):
        bigram = f"{words[i]} {words[i+1]}"
        bigrams[bigram] += 1
    for i in range(len(words) - 2):
        trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
        trigrams[trigram] += 1

print("Filtering and saving dataset...")
# Keep top bigrams and trigrams to limit file size (expanded for Phase B6)
top_bigrams = {k: v for k, v in bigrams.most_common(1500000) if v > 1}
top_trigrams = {k: v for k, v in trigrams.most_common(1500000) if v > 1}

dataset = {
    "metadata": {
        "source": "Tatoeba Esperanto Corpus",
        "total_sentences": len(sentences),
        "unique_vocabulary": len(unique_vocab),
        "bigrams_count": len(top_bigrams),
        "trigrams_count": len(top_trigrams)
    },
    "bigrams": top_bigrams,
    "trigrams": top_trigrams
}

out_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'context_frequency.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(dataset, f, ensure_ascii=False, separators=(',', ':'))

print(f"Saved dataset to {out_path}")
print(f"File size: {os.path.getsize(out_path) / 1024 / 1024:.2f} MB")

print("\n--- STATS ---")
print(f"Total phrases: {len(sentences)}")
print(f"Unique vocab: {len(unique_vocab)}")
print("Top 10 Bigrams:")
for k, v in bigrams.most_common(10):
    print(f"  {k}: {v}")
print("Top 10 Trigrams:")
for k, v in trigrams.most_common(10):
    print(f"  {k}: {v}")

print("\nReal Examples for Ambiguity Testing:")
examples = ["ŝi kantis", "ŝi diris", "ĝi estas", "mi vidis ŝin", "ĉi tio"]
for ex in examples:
    print(f"  '{ex}' -> {bigrams.get(ex, 0)} occurrences")
