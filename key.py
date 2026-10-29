#!/usr/bin/env python3
#Create the one key used for the whole experiment.
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detector import generate_key, save_key

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="keys/key.hex")
    args = ap.parse_args()

    out = Path(args.out)
    if out.exists():
        sys.exit(f"{out} already exists. Do not make a new one.")
    save_key(out, generate_key())
    print(f"wrote {out}")

if __name__ == "__main__":
    main()
