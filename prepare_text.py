#!/usr/bin/env python3
"""
preps the 315 passages and the calibration/evaluation split.

Input: data/books/*.txt
Output: data/passages, manifest.csv, split_info.json
"""
import argparse
import csv
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detector import tokenize  # noqa: E402

GROUPS = {"30-99": (30, 99), "100-199": (100, 199), "200-400": (200, 400)}
PER_GROUP_PER_SET = 50
WM_PER_SET = {"calibration": 5, "evaluation": 10}
START = re.compile(r"\*\*\* ?START OF (?:THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.I | re.S)
END = re.compile(r"\*\*\* ?END OF (?:THE|THIS) PROJECT GUTENBERG", re.I)
SENT_SPLIT = re.compile(r"(?<=[.!?])[\"'”’)]*\s+")
FOOTNOTE_BODY = re.compile(r"\[\d+\]")         # if a paragraph starts with [12], it is a footnote
FOOTNOTE_MARK = re.compile(r"\s*\[\d+\]")      # inline references
FOOTNOTE_NUM = re.compile(r"(?<=[a-z])\d+\b")  # number stuck to a word, like "cloisters11"
TRANSCRIBER = re.compile(r"Gutenberg|etext", re.I)  # transcriber's notes about the file

# load sentences from a book, removing Gutenberg header+footer, short lines, and all-caps lines. returns a list of sentences.
def load_sentences(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    m = START.search(raw)
    if m:
        raw = raw[m.end():]
    m = END.search(raw)
    if m:
        raw = raw[:m.start()]
    sents = []
    for para in re.split(r"\n\s*\n", raw):
        para = " ".join(para.split())
        if FOOTNOTE_BODY.match(para) or TRANSCRIBER.search(para):
            continue
        para = FOOTNOTE_MARK.sub("", para)
        para = FOOTNOTE_NUM.sub("", para)
        if len(tokenize(para)) < 12:
            continue
        if para.isupper():
            continue
        sents.extend(s for s in SENT_SPLIT.split(para) if s)
    return sents

# nice print of a list of sentences, one per line, with a blank line between each sentence.
def candidates(sents: list[str], rng: random.Random) -> dict[str, list[str]]:
    """Non-overlapping contiguous sentence spans, per length group."""
    n = len(sents)
    lens = [len(tokenize(s)) for s in sents]
    used = [False] * n
    out = {g: [] for g in GROUPS}
    for g, (lo, hi) in GROUPS.items():
        i = rng.randint(0, 30)
        while i < n:
            target = rng.randint(lo, hi)
            j, wc = i, 0
            while j < n and wc < target and not used[j]:
                wc += lens[j]
                j += 1
            if lo <= wc <= hi and not any(used[i:j]):
                for k in range(i, j):
                    used[k] = True
                out[g].append(" ".join(sents[i:j]))
                i = j + rng.randint(15, 120)
            else:
                i += 1
    return out

# list of (book, text) pairs, round-robin across books, up to k total
def round_robin(pool: dict[str, list[str]], k: int, rng: random.Random):
    """Take k items spreading across books. pool: book -> list of texts."""
    pool = {b: rng.sample(t, len(t)) for b, t in pool.items()}
    chosen, books = [], sorted(pool)
    while len(chosen) < k and any(pool.values()):
        for b in books:
            if pool[b] and len(chosen) < k:
                chosen.append((b, pool[b].pop()))
    return chosen

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--books", default="data/books")
    ap.add_argument("--out", default="data")
    ap.add_argument("--seed", type=int, default=20261009)
    ap.add_argument("--forgery-seed", type=int, default=7)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    books = sorted(Path(args.books).glob("*.txt"))
    if len(books) < 6:
        sys.exit(f"Need at least 6 books in {args.books} (found {len(books)}); "
                 "aim for 8-12 so each set has several independent sources.")
    #shuffle books and assign to calibration/evaluation sets at random, so that each set has several sources
    shuffled = books[:]
    rng.shuffle(shuffled)
    book_set = {b.stem: ("calibration" if i % 2 == 0 else "evaluation")
                for i, b in enumerate(shuffled)}

    cand = {s: {g: defaultdict(list) for g in GROUPS} for s in WM_PER_SET}
    for b in books:
        c = candidates(load_sentences(b), rng)
        for g, texts in c.items():
            cand[book_set[b.stem]][g][b.stem].extend(texts)

    rows, seen = [], set()
    out = Path(args.out)
    (out / "passages").mkdir(parents=True, exist_ok=True)

    # helper to add a passage to the output and manifest
    def add(pid, setname, coll, group, book, text):
        key = " ".join(tokenize(text))
        if key in seen:
            sys.exit(f"duplicate passage {pid}")
        seen.add(key)
        (out / "passages" / f"{pid}.txt").write_text(text + "\n", encoding="utf-8")
        rows.append({"id": pid, "set": setname, "collection": coll,
                     "length_group": group, "book": book,
                     "total_words": len(tokenize(text)),
                     "distinct_words": len(set(tokenize(text))), "forgery_selected": ""})

    for s, n_wm in WM_PER_SET.items():
        # watermarking passages first (from the 100-199 pool
        wm = round_robin(cand[s]["100-199"], n_wm, rng)
        if len(wm) < n_wm:
            sys.exit(f"{s}: only {len(wm)} watermarking candidates; add books")
        for i, (b, t) in enumerate(wm, 1):
            add(f"{s[:3]}_wm_{i:02d}", s, "watermark", "100-199", b, t)
            cand[s]["100-199"][b] = [x for x in cand[s]["100-199"][b] if x != t]
        for g in GROUPS:
            got = round_robin(cand[s][g], PER_GROUP_PER_SET, rng)
            if len(got) < PER_GROUP_PER_SET:
                sys.exit(f"{s}/{g}: only {len(got)} of {PER_GROUP_PER_SET} "
                         "unmarked passages; add more or longer books")
            for i, (b, t) in enumerate(got, 1):
                add(f"{s[:3]}_un_{g}_{i:02d}", s, "unmarked", g, b, t)

    # forgery selection
    eval_wm = sorted(r["id"] for r in rows if r["set"] == "evaluation"
                     and r["collection"] == "watermark")
    picked = set(random.Random(args.forgery_seed).sample(eval_wm, 5))
    for r in rows:
        if r["id"] in picked:
            r["forgery_selected"] = "yes"

    with open(out / "manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    info = {
        "books": {b.stem: book_set[b.stem] for b in books},
        "book_to_set_method": f"files shuffled with random.Random({args.seed}), alternating calibration/evaluation",
        "forgery_selection_method": f"random.Random({args.forgery_seed}).sample(sorted evaluation watermark ids, 5), run at data prep time",
        "forgery_selected": sorted(picked),
        "counts": {f"{s}/{c}": sum(r['set'] == s and r['collection'] == c for r in rows)
                   for s in WM_PER_SET for c in ("unmarked", "watermark")},
    }
    # creates split_info.json with the book assignments and counts of passages per collection
    (out / "split_info.json").write_text(json.dumps(info, indent=2))
    print(json.dumps(info["counts"], indent=2))
    print("forgery-selected:", ", ".join(sorted(picked)))

if __name__ == "__main__":
    main()
