import json
import re
import urllib.request
import bz2
import random
import os

print("Loading datasets...")
context_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'context_frequency.json')
with open(context_path, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

bigrams = dataset['bigrams']
trigrams = dataset['trigrams']

# Unigram frequencies derived from bigrams
unigrams = {}
for bg, count in bigrams.items():
    w1, w2 = bg.split()
    unigrams[w1] = unigrams.get(w1, 0) + count
    unigrams[w2] = unigrams.get(w2, 0) + count

ambiguities = {
    "Ii": ["ĉi", "ĝi", "ŝi"],
    "Iin": ["ĝin", "ŝin"],
    "Iia": ["ĉia", "ĝia", "ŝia"],
    "ruIa": ["ruĝa", "ruĵa", "ruŝa"],
    "buIo": ["buĉo", "buŝo"],
    "vizaIo": ["vizaĝo", "vizaĵon"],
    "infanaIo": ["infanaĉo", "infanaĝo", "infanaĵo"]
}

# Download a tiny sample of sentences to test context
url = "https://downloads.tatoeba.org/exports/per_language/epo/epo_sentences.tsv.bz2"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
response = urllib.request.urlopen(req)
compressed_data = response.read()
data = bz2.decompress(compressed_data).decode('utf-8')

sentences = []
for line in data.split('\n'):
    parts = line.split('\t')
    if len(parts) >= 3:
        sentences.append(parts[2].strip().lower())

def tokenize(text):
    text = re.sub(r'[^\w\^]', ' ', text)
    return text.split()

print("Generating Test Cases...")
test_cases = []
for sent in sentences:
    words = tokenize(sent)
    for i, w in enumerate(words):
        for damaged, candidates in ambiguities.items():
            if w in candidates:
                prev2 = words[i-2] if i > 1 else None
                prev_w = words[i-1] if i > 0 else None
                next_w = words[i+1] if i < len(words)-1 else None
                next2 = words[i+2] if i < len(words)-2 else None
                
                test_cases.append({
                    "damaged": damaged,
                    "correct": w,
                    "candidates": candidates,
                    "prev2": prev2,
                    "prev": prev_w,
                    "next": next_w,
                    "next2": next2,
                    "sentence": sent
                })
                break

random.seed(42)
sampled_cases = random.sample(test_cases, min(500, len(test_cases)))

# Grammatical Rules Dictionary
grammar_rules = {
    "ĉi": lambda p, n: 100000 if n in ["tiu", "tie", "tio", "ĉi", "ĉia", "ĉies"] or p in ["tiu", "tie", "tio"] else 0,
    "ŝi": lambda p, n: 100000 if n and (n.endswith("is") or n.endswith("as") or n.endswith("os") or n.endswith("us")) else 0,
    "ĝi": lambda p, n: 100000 if n in ["estas", "havas", "povas"] else 0,
    "ĝin": lambda p, n: 100000 if p and (p.endswith("is") or p.endswith("as") or p.endswith("os") or p.endswith("us") or p.endswith("i")) else 0,
    "ŝin": lambda p, n: 100000 if p and (p.endswith("is") or p.endswith("as") or p.endswith("os") or p.endswith("us") or p.endswith("i")) else 0
}

def score_unigram(candidates):
    return {c: unigrams.get(c, 0) for c in candidates}

def score_bigram(candidates, prev_w, next_w):
    scores = {}
    for c in candidates:
        s = 0
        if prev_w: s += bigrams.get(f"{prev_w} {c}", 0)
        if next_w: s += bigrams.get(f"{c} {next_w}", 0)
        scores[c] = s
    return scores

def score_trigram(candidates, prev2, prev_w, next_w, next2):
    scores = {}
    for c in candidates:
        s = 0
        if prev2 and prev_w: s += trigrams.get(f"{prev2} {prev_w} {c}", 0)
        if prev_w and next_w: s += trigrams.get(f"{prev_w} {c} {next_w}", 0)
        if next_w and next2: s += trigrams.get(f"{c} {next_w} {next2}", 0)
        scores[c] = s
    return scores

def score_grammar(candidates, prev_w, next_w):
    scores = {}
    for c in candidates:
        rule_fn = grammar_rules.get(c)
        if rule_fn:
            scores[c] = rule_fn(prev_w, next_w)
        else:
            scores[c] = 0
    return scores

def decide(scores_dict):
    sorted_s = sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)
    top_s = sorted_s[0][1]
    sec_s = sorted_s[1][1] if len(sorted_s) > 1 else 0
    total = top_s + sec_s
    if total == 0:
        return None, True # MR due to zero confidence
    conf = top_s / total
    return sorted_s[0][0], conf < 0.85

results = {
    "sysA_mr": 0, "sysB_mr": 0, "sysC_mr": 0, "sysD_mr": 0,
    "sysB_correct": 0, "sysC_correct": 0, "sysD_correct": 0,
    "remaining_analysis": {"trigram_solvable": 0, "grammar_solvable": 0, "unresolvable": 0}
}

for case in sampled_cases:
    cands = case["candidates"]
    cor = case["correct"]
    
    # Sys A
    sA = score_unigram(cands)
    wA, mrA = decide(sA)
    if mrA: results["sysA_mr"] += 1
    
    # Sys B (Bigram only)
    sB = score_bigram(cands, case["prev"], case["next"])
    wB, mrB = decide(sB)
    if not wB: wB, mrB = wA, mrA
    if mrB: results["sysB_mr"] += 1
    if wB == cor: results["sysB_correct"] += 1
        
    # Sys C (Trigram only)
    sC = score_trigram(cands, case["prev2"], case["prev"], case["next"], case["next2"])
    wC, mrC = decide(sC)
    if not wC: wC, mrC = wA, mrA
    if mrC: results["sysC_mr"] += 1
    if wC == cor: results["sysC_correct"] += 1
        
    # Sys D (Bigram + Trigram + Grammar + Unigram Fallback)
    sD = {}
    sG = score_grammar(cands, case["prev"], case["next"])
    for c in cands:
        sD[c] = sB.get(c,0) + (sC.get(c,0)*5) + sG.get(c,0)
    wD, mrD = decide(sD)
    if not wD: wD, mrD = wA, mrA
    if mrD: 
        results["sysD_mr"] += 1
        # Analyze why it failed
        # Could trigrams have solved it if we had a bigger dataset?
        if sC.get(cor, 0) > 0:
            results["remaining_analysis"]["trigram_solvable"] += 1
        elif sG.get(cor, 0) > 0:
            results["remaining_analysis"]["grammar_solvable"] += 1
        else:
            results["remaining_analysis"]["unresolvable"] += 1
            
    if wD == cor: results["sysD_correct"] += 1

print("\n--- BENCHMARK RESULTS (500 Cases) ---")
print(f"System A (Unigram) Manual Reviews: {results['sysA_mr']}")
print(f"System B (Bigram) MRs: {results['sysB_mr']} | Acc: {results['sysB_correct']/500*100}%")
print(f"System C (Trigram) MRs: {results['sysC_mr']} | Acc: {results['sysC_correct']/500*100}%")
print(f"System D (Combined) MRs: {results['sysD_mr']} | Acc: {results['sysD_correct']/500*100}%")

redB = (results['sysA_mr'] - results['sysB_mr']) / results['sysA_mr'] * 100
redC = (results['sysA_mr'] - results['sysC_mr']) / results['sysA_mr'] * 100
redD = (results['sysA_mr'] - results['sysD_mr']) / results['sysA_mr'] * 100

print(f"Reduction B: {redB:.2f}% | C: {redC:.2f}% | D: {redD:.2f}%")
print("\n--- REMAINING CASES ANALYSIS (Sys D) ---")
print(results["remaining_analysis"])

with open("/tmp/benchmark_results_v2.json", "w") as f:
    json.dump({
        "totals": 500,
        "results": results,
        "reductions": {"B": redB, "C": redC, "D": redD}
    }, f)
