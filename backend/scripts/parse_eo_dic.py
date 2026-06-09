import os

HUNSPELL_DIC = os.path.join(os.path.dirname(__file__), "..", "data", "hunspell", "eo.dic")
OUT_DICT = os.path.join(os.path.dirname(__file__), "..", "data", "esperanto_roots.txt")

def parse_dic():
    roots = set()
    with open(HUNSPELL_DIC, "r", encoding="utf-8") as f:
        # Skip first line (count)
        next(f)
        for line in f:
            word = line.strip().split("/")[0]
            if word:
                roots.add(word.lower())
                
    # Add our fallback words just in case
    fallback_words = [
        "eŭrop", "skrib", "aĵ", "ruĝ", "reĝ", "nask", "iĝ", "aŭtism", "aŭtist",
        "ankaŭ", "hieraŭ", "morgaŭ", "ĉar", "ĉiu", "ŝi", "feliĉa", "kvazaŭ",
        "eĉ", "ĉiuj", "ŝin", "hodiaŭ", "vivaĉas", "ĉu", "vekiĝis", "registriĝi",
        "baldaŭ", "loĝis", "serĉis"
    ]
    for fw in fallback_words:
        roots.add(fw)

    with open(OUT_DICT, "w", encoding="utf-8") as f:
        for root in sorted(list(roots)):
            f.write(root + "\n")
            
    print(f"Parsed {len(roots)} roots from eo.dic and saved to {OUT_DICT}")

if __name__ == "__main__":
    parse_dic()
