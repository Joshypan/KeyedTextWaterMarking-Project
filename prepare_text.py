#!/usr/bin/env python3
"""
preps the 315 passages and the calibration/evaluation split.

Input: data/books/*.txt
Output: data/passages, manifest.csv, split_info.json
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detector import tokenize  # noqa: E402,F401

GROUPS = {"30-99": (30, 99), "100-199": (100, 199), "200-400": (200, 400)}
PER_GROUP_PER_SET = 50
WM_PER_SET = {"calibration": 5, "evaluation": 10}


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

    # list the books found
    print(f"Found {len(books)} books:")
    for b in books:
        print(" ", b.stem)


if __name__ == "__main__":
    main()
