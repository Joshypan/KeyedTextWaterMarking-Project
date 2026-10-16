#!/usr/bin/env python3
"""
preps the 315 passages and the calibration/evaluation split.

Input: data/books/*.txt
Output: data/passages, manifest.csv, split_info.json
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detector import tokenize  # noqa: E402

GROUPS = {"30-99": (30, 99), "100-199": (100, 199), "200-400": (200, 400)}
PER_GROUP_PER_SET = 50
WM_PER_SET = {"calibration": 5, "evaluation": 10}
# this is the number of words to use for the watermarking of each passage. 
# 5 is good to get a good sign, and 10 is enough to get a strong sign. 15 is overkill and makes the passages too long.
START = re.compile(r"\*\*\* ?START OF (?:THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.I | re.S)
END = re.compile(r"\*\*\* ?END OF (?:THE|THIS) PROJECT GUTENBERG", re.I)
SENT_SPLIT = re.compile(r"(?<=[.!?])[\"'”’)]*\s+")

# loads sentences from files
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
        if len(tokenize(para)) < 12:
            continue
        if para.isupper():
            continue
        sents.extend(s for s in SENT_SPLIT.split(para) if s)
    return sents


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--books", default="data/books")
    ap.add_argument("--out", default="data")
    ap.add_argument("--seed", type=int, default=20261009)
    ap.add_argument("--forgery-seed", type=int, default=7)
    args = ap.parse_args()

    books = sorted(Path(args.books).glob("*.txt"))
    if len(books) < 6:
        sys.exit(f"Need at least 6 books in {args.books} (found {len(books)}); "
                 "aim for 8-12 so each set has several independent sources.")

    #sentence counts, and finds the first/last sentence of each book
    for b in books:
        sents = load_sentences(b)
        print(f"{b.stem}: {len(sents)} sentences")
        print("  first:", sents[0][:80])
        print("  last: ", sents[-1][:80])


if __name__ == "__main__":
    main()
