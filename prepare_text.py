#!/usr/bin/env python3
"""
preps the 315 passages and the calibration/evaluation split.

Input: data/books/*.txt
Output: data/passages, manifest.csv, split_info.json
"""
import argparse
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
        if len(tokenize(para)) < 12:      # headings, page furniture, tiny lines
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

    shuffled = books[:]
    rng.shuffle(shuffled)
    book_set = {b.stem: ("calibration" if i % 2 == 0 else "evaluation")
                for i, b in enumerate(shuffled)}

    cand = {s: {g: defaultdict(list) for g in GROUPS} for s in WM_PER_SET}
    for b in books:
        c = candidates(load_sentences(b), rng)
        for g, texts in c.items():
            cand[book_set[b.stem]][g][b.stem].extend(texts)

    # candidates per book and group, each set needs >= 50 per
    # group (and 100-199 gets 50 + the watermarking passages on top)
    for s in WM_PER_SET:
        print(f"{s}:")
        for g in GROUPS:
            per_book = {b: len(t) for b, t in sorted(cand[s][g].items())}
            print(f"  {g:>8}: total {sum(per_book.values()):4d}  {per_book}")


if __name__ == "__main__":
    main()
