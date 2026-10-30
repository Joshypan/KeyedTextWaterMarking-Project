#!/usr/bin/env python3
#Score passages, choose and freeze the threshold, then run the evaluation.

import argparse
import csv
import difflib
import hashlib
import json
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detector import is_flagged, load_key, score_text, tokenize, word_color  # noqa: E402

DATA = Path("data")
RESULTS = Path("results")
REVIEW = Path("review")
SETTINGS = RESULTS / "settings.json"
GROUPS = ["30-99", "100-199", "200-400"]
CANDIDATE_THRESHOLDS = ["0.55", "0.60", "0.65"]


# helper fucntions
def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_manifest() -> list[dict]:
    with open(DATA / "manifest.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_passage(pid: str) -> str:
    return (DATA / "passages" / f"{pid}.txt").read_text(encoding="utf-8")


def final_path(pid: str) -> Path:
    return DATA / "watermarked" / pid / "final.txt"


def file_hash(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def changed_words(original: str, edited: str) -> int:
    """Word-level edit count on normalized words (difflib alignment).
    Each replaced, deleted or inserted run counts as its longer side, so
    swapping 1 word for 1 word counts 1, and swapping 1 for 3 counts 3."""
    a, b = tokenize(original), tokenize(edited)
    n = 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if op != "equal":
            n += max(i2 - i1, j2 - j1)
    return n

def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

# scoring
def score_one(text: str, key: bytes) -> dict:
    s = score_text(text, key)
    return {"total_words": s.total, "distinct_words": s.distinct,
            "green": s.green, "fraction": f"{s.fraction:.4f}"}

def score_set(setname: str, key: bytes) -> list[dict]:
    """Score every passage in a set. Watermarking passages get two rows:
    the original and, if it exists, the final edited version."""
    rows = []
    for m in load_manifest():
        if m["set"] != setname:
            continue
        base = {"id": m["id"], "set": m["set"], "collection": m["collection"],
                "length_group": m["length_group"], "book": m["book"]}
        original = read_passage(m["id"])
        rows.append({**base, "version": "original", **score_one(original, key),
                     "changed_words": 0})
        if m["collection"] == "watermark" and final_path(m["id"]).exists():
            edited = final_path(m["id"]).read_text(encoding="utf-8")
            rows.append({**base, "version": "final", **score_one(edited, key),
                         "changed_words": changed_words(original, edited)})
    return rows

def flagged(row: dict, threshold) -> bool:
    return is_flagged(int(row["green"]), int(row["total_words"]), threshold)

# commands
def cmd_calibrate(args):
    key = load_key(args.key)
    rows = score_set("calibration", key)
    write_csv(RESULTS / "calibration_scores.csv", rows)

    unmarked = [r for r in rows if r["collection"] == "unmarked"]
    outputs = [r for r in rows if r["version"] == "final"]
    table = []
    for t in args.thresholds:
        row = {"threshold": t,
               "flagged_unmarked": sum(flagged(r, t) for r in unmarked),
               "unmarked_tested": len(unmarked),
               "unflagged_outputs": sum(not flagged(r, t) for r in outputs),
               "outputs_tested": len(outputs)}
        table.append(row)
    write_csv(RESULTS / "calibration_thresholds.csv", table)

    run = {"command": "calibrate", "ran_at": now(), "key_file": args.key,
           "detector_sha256": file_hash(Path(__file__).resolve().parent / "detector.py"),
           "thresholds": args.thresholds, "final_outputs_found": len(outputs)}
    (RESULTS / "calibration_run.json").write_text(json.dumps(run, indent=2) + "\n")

    print(f"scored {len(unmarked)} unmarked and {len(outputs)} watermarked calibration passages")
    print(f"{'threshold':>9}  flagged unmarked  unflagged outputs")
    for r in table:
        print(f"{r['threshold']:>9}  {r['flagged_unmarked']:>7} / {r['unmarked_tested']:<6}"
              f"  {r['unflagged_outputs']:>7} / {r['outputs_tested']}")
    if not outputs:
        print("no data/watermarked/<id>/final.txt yet: practice watermarking (step 4), then re-run")

# freeze the settings before evaluation
def cmd_fix(args):
    if SETTINGS.exists():
        sys.exit(f"{SETTINGS} already exists: the settings are frozen. If you change the "
                 "design after evaluation, keep the old results and report the new run separately.")
    key = load_key(args.key)
    try:
        Fraction(args.threshold), Fraction(args.target)
    except ValueError:
        sys.exit("--threshold and --target must be numbers, e.g. 0.65")
    settings = {
        "fixed_at": now(),
        "key_file": args.key,
        "detector_sha256": file_hash(Path(__file__).resolve().parent / "detector.py"),
        "word_rules": "detector.tokenize: remove Unicode Cf characters, NFKC, curly "
                      "apostrophes to ', words = letters/digits with inner apostrophes, casefold",
        "threshold": args.threshold,
        "flag_rule": "flag when green/total is strictly greater than threshold",
        "watermark_target": args.target,
        "stopping_rule": args.stop,
    }
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(settings, indent=2) + "\n")
    print(f"froze settings in {SETTINGS}:")
    print(json.dumps(settings, indent=2))

def load_reviews(setname: str) -> dict[str, dict]:
    sheet = REVIEW / setname / "quality_reviews.csv"
    if not sheet.exists():
        return {}
    with open(sheet, newline="", encoding="utf-8") as f:
        return {r["id"]: r for r in csv.DictReader(f)}

def cmd_evaluate(args):
    if not SETTINGS.exists():
        sys.exit("run `evaluate.py fix` first; evaluation uses only frozen settings")
    settings = json.loads(SETTINGS.read_text())
    if args.key != settings["key_file"]:
        sys.exit(f"use the key recorded in settings.json: {settings['key_file']}")
    key = load_key(args.key)
    if file_hash(Path(__file__).resolve().parent / "detector.py") != settings["detector_sha256"]:
        sys.exit("detector.py changed after the settings were fixed")

    out = RESULTS / ("evaluation" if not args.rerun else f"evaluation_rerun_{args.rerun}")
    if out.exists():
        sys.exit(f"{out} already exists; original results are kept. "
                 "Use --rerun NAME for a separate, separately reported run.")

    t, target = settings["threshold"], Fraction(settings["watermark_target"])
    rows = score_set("evaluation", key)
    reviews = load_reviews("evaluation")
    for r in rows:
        r["flagged"] = "yes" if flagged(r, t) else "no"
        if r["version"] == "final":
            rv = reviews.get(r["id"], {})
            r["meaning_preserved"] = rv.get("meaning_preserved", "").strip().lower()
            r["readable"] = rv.get("readable", "").strip().lower()
            r["usable"] = "yes" if (r["meaning_preserved"], r["readable"]) == ("yes", "yes") else "no"
            r["reached_target"] = ("yes" if Fraction(int(r["green"]), int(r["total_words"])) >= target
                                   else "no")
    # same columns on every row so the CSV lines up
    cols = list(dict.fromkeys(k for r in rows for k in r))
    rows = [{c: r.get(c, "") for c in cols} for r in rows]

    unmarked = [r for r in rows if r["collection"] == "unmarked"]
    wm_ids = sorted({r["id"] for r in rows if r["collection"] == "watermark"})
    finals = {r["id"]: r for r in rows if r["version"] == "final"}
    originals = {r["id"]: r for r in rows if r["version"] == "original"}
    missing = [i for i in wm_ids if i not in finals]
    unreviewed = [i for i in finals if not finals[i]["meaning_preserved"] or not finals[i]["readable"]]
    forgery = {m["id"] for m in load_manifest() if m["forgery_selected"] == "yes"}

    n_fp = sum(r["flagged"] == "yes" for r in unmarked)
    n_det = sum(f["flagged"] == "yes" for f in finals.values())
    n_use = sum(f["flagged"] == "yes" and f["usable"] == "yes" for f in finals.values())
    n_hit = sum(f["reached_target"] == "yes" for f in finals.values())
    n = len(unmarked)
    summary = {
        "ran_at": now(),
        "settings": settings,
        "false_positive_rate": {"flagged": n_fp, "tested": n, "rate": n_fp / n,
                                "rule_of_three_upper": 3 / n if n_fp == 0 else None},
        "by_length_group": {g: {"flagged": sum(r["flagged"] == "yes" for r in unmarked
                                               if r["length_group"] == g),
                                "tested": sum(r["length_group"] == g for r in unmarked)}
                            for g in GROUPS},
        # missing outputs count as failed attempts: the denominator is all attempts
        "detection_rate": {"flagged": n_det, "attempts": len(wm_ids)},
        "usable_success_rate": {"flagged_and_usable": n_use, "attempts": len(wm_ids)},
        "reached_target": {"count": n_hit, "attempts": len(wm_ids)},
        "missing_outputs": missing,
        "unreviewed_outputs": unreviewed,
        "per_passage": [{"id": i,
                         "forgery_selected": i in forgery,
                         "before": originals[i]["fraction"],
                         "after": finals[i]["fraction"] if i in finals else None,
                         "changed_words": finals[i]["changed_words"] if i in finals else None,
                         "flagged_after": finals[i]["flagged"] if i in finals else "no",
                         "usable": finals[i]["usable"] if i in finals else "no"}
                        for i in wm_ids],
    }
    out.mkdir(parents=True)
    write_csv(out / "scores.csv", rows)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    bound = f" (95% upper bound about 3/{n} = {3 / n:.3f})" if n_fp == 0 else ""
    print(f"false positives: {n_fp}/{n} = {n_fp / n:.3f}{bound}")
    for g, c in summary["by_length_group"].items():
        print(f"  {g:>8}: {c['flagged']}/{c['tested']} flagged")
    print(f"detection rate: {n_det}/{len(wm_ids)}   usable success: {n_use}/{len(wm_ids)}   "
          f"reached target: {n_hit}/{len(wm_ids)}")
    for p in summary["per_passage"]:
        print(f"  {p['id']}: {p['before']} -> {p['after']}  changed {p['changed_words']}  "
              f"flagged {p['flagged_after']}  usable {p['usable']}")
    if missing:
        print("missing final.txt (counted as failed):", ", ".join(missing))
    if unreviewed:
        print("no quality review yet (counted as not usable):", ", ".join(unreviewed))
    print(f"saved to {out}/")

# score one file while editing, and list its red words
def cmd_score(args):
    if not Path(args.file).exists():
        sys.exit(f"{args.file} does not exist; save your edited version there first")
    key = load_key(args.key)
    text = Path(args.file).read_text(encoding="utf-8")
    s = score_text(text, key)
    red = sorted({w for w in tokenize(text) if not word_color(w, key)})
    print(f"green {s.green}/{s.total} = {s.fraction:.3f}")
    print("red words:", ", ".join(red))

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("calibrate", help="score calibration passages, compare thresholds")
    p.add_argument("--key", required=True)
    p.add_argument("--thresholds", nargs="+", default=CANDIDATE_THRESHOLDS)
    p.set_defaults(func=cmd_calibrate)

    p = sub.add_parser("fix", help="freeze the settings before evaluation")
    p.add_argument("--key", required=True)
    p.add_argument("--threshold", required=True)
    p.add_argument("--target", required=True, help="green fraction the editor aims for")
    p.add_argument("--stop", required=True, help="stopping rule, in words")
    p.set_defaults(func=cmd_fix)

    p = sub.add_parser("evaluate", help="score the evaluation set with frozen settings")
    p.add_argument("--key", required=True)
    p.add_argument("--rerun", help="name for a separate run after a design change")
    p.set_defaults(func=cmd_evaluate)

    p = sub.add_parser("score", help="score one file and list its red words")
    p.add_argument("file")
    p.add_argument("--key", required=True)
    p.set_defaults(func=cmd_score)

    args = ap.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
