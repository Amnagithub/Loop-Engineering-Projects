#!/usr/bin/env python3
"""loop12 scan.py - the deterministic evidence ring of the Dreaming Loop.

The dreaming loop's job is NOT to judge. This scanner's job is to *prove*,
from the dated records in the loops' own logs, that some failure or
correction appears more than once - and to say exactly where.

It reads two corpora:

  1. REAL   : every <loop-root>/loop*/progress.md and loop*/loop-log.md the
              earlier projects left behind (loop12's own bookkeeping is
              skipped so the loop never dreams about itself).
  2. DRILL  : <loop-root>/loop12/observed-runs.md - a dated fleet log that is
              loop12's input fixture (the deliberately planted repeated
              failure lives here; see loop12/README.md).

Each line that carries a YYYY-MM-DD date opens a "record" (the line plus the
following lines up to the next dated line). Records whose text carries
failure/correction vocabulary are kept, normalized into a stable signature
(dates, digits and markdown stripped), and grouped. Any signature that maps
back to TWO OR MORE distinct dated records is a proven repeat and is emitted
with full citations (file, line, date, run, excerpt).

The ring never lies: it only reports what it can cite verbatim. Judgment
(which repeat is worth a rule, what the smallest rule is) is the Dreamer's,
and the Checker re-derives every citation from the files.

Usage (canonical interpreter: C:\\Python314\\python.exe):
    python scan.py --loop-root <abs loopprojects> [--extra <file>]
                   [--from 2026-09-02] [--until 2026-09-03]
                   [--json | --self-test]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# vocabulary / normalisation
# --------------------------------------------------------------------------- #

DATE_RE = re.compile(r"(?<!\d)(20\d{2}-\d{2}-\d{2})(?!\d)")
# words that mark a record as a failure or a correction (vs. a plain SUCCESS row)
RELEVANT_RE = re.compile(
    r"(fail\w*|error\w*|bug\w*|crash\w*|broke\w*|wrong\b|stub\b|stall\w*|"
    r"stuck\b|hang\w*|block\w*|refus\w*|denied\b|reject\w*|not found\b|"
    r"missing\b|could not\b|couldn'?t\b|would not\b|wouldn'?t\b|escalat\w*|"
    r"needs human|untrusted\b|trust prompt|exhausted\b|timeout\b|fix\w*|"
    r"correct\w*|lesson\b|rediscover\w*)"
)
RUN_RE = re.compile(r"(?:Run\s*#?(\d+)|^\s*\|?\s*(\d+)\s*\|)")

STRIP = re.compile(r"[^a-z0-9]+")
DIGIT = re.compile(r"[0-9]+")

MAX_BODY_LINES = 8          # how far a record extends past its date line
MIN_SIG_LEN = 12            # drop signatures too short to be meaningful


def _run_of(line: str) -> str | None:
    m = RUN_RE.search(line)
    if not m:
        return None
    return m.group(1) or m.group(2)


def _signature(text: str) -> str:
    t = text.lower()
    t = DATE_RE.sub(" ", t)          # drop dates
    t = DIGIT.sub("", t)             # drop run numbers / counts / times
    t = STRIP.sub(" ", t)            # drop markdown + punctuation
    t = re.sub(r"\s+", " ", t).strip()
    return t


# --------------------------------------------------------------------------- #
# corpus walk
# --------------------------------------------------------------------------- #

def is_corpus_file(p: Path, loop_root: Path) -> bool:
    """progress.md / loop-log.md of any loop EXCEPT loop12 (not its own bookkeeping)."""
    try:
        rel = p.relative_to(loop_root)
    except ValueError:
        return False
    parts = rel.parts
    if len(parts) < 2 or not parts[0].startswith("loop"):
        return False
    if parts[0] == "loop12":
        return False
    return p.name in ("progress.md", "loop-log.md")


def collect_files(loop_root: Path, extra: Path | None) -> list[Path]:
    files: list[Path] = []
    for p in sorted(loop_root.glob("loop*/*.md")):
        if is_corpus_file(p, loop_root):
            files.append(p)
    if extra and extra.exists():
        files.append(extra)
    return files


def parse_records(path: Path) -> list[dict]:
    """Split a log into dated records. Each record = date line + up to
    MAX_BODY_LINES following non-date lines."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    records: list[dict] = []
    cur = None
    for i, raw in enumerate(lines, start=1):
        line = raw.strip()
        dm = DATE_RE.search(line)
        if dm:
            if cur is not None:
                records.append(cur)
            cur = {
                "file": str(path).replace("\\", "/"),
                "line": i,
                "date": dm.group(1),
                "run": _run_of(line),
                "text": line,
                "body": [],
            }
        elif cur is not None and len(cur["body"]) < MAX_BODY_LINES:
            if line:
                cur["body"].append(line)
    if cur is not None:
        records.append(cur)
    return records


def in_window(rec: dict, after: str, until: str) -> bool:
    return after < rec["date"] <= until


def scan(loop_root: Path, after: str, until: str, extra: Path | None) -> dict:
    files = collect_files(loop_root, extra)
    all_records: list[dict] = []
    for f in files:
        for rec in parse_records(f):
            rec["full"] = " | ".join([rec["text"]] + rec["body"])
            all_records.append(rec)

    windowed = [r for r in all_records if in_window(r, after, until)]

    # candidates = windowed records whose text carries failure/correction vocab
    candidates = [r for r in windowed if RELEVANT_RE.search(r["full"].lower())]

    # cluster by normalised signature
    groups: dict[str, list[dict]] = {}
    for r in candidates:
        sig = _signature(r["full"])
        if len(sig) < MIN_SIG_LEN:
            continue
        groups.setdefault(sig, []).append(r)

    clusters = []
    for sig, recs in groups.items():
        if len(recs) < 2:
            continue
        # one citation per distinct dated record
        clusters.append({
            "signature": sig,
            "count": len(recs),
            "records": [
                {
                    "file": r["file"],
                    "line": r["line"],
                    "date": r["date"],
                    "run": r.get("run"),
                    "excerpt": (r["full"] or "")[:300],
                }
                for r in sorted(recs, key=lambda x: x["date"])
            ],
        })

    clusters.sort(key=lambda c: (-c["count"], max(r["date"] for r in c["records"])))

    return {
        "window": {"after": after, "until": until},
        "files_scanned": [str(f).replace("\\", "/") for f in files],
        "records_total": len(all_records),
        "records_in_window": len(windowed),
        "candidate_records": len(candidates),
        "clusters": clusters,
        "window_records": [
            {
                "file": r["file"], "line": r["line"], "date": r["date"],
                "run": r.get("run"),
                "excerpt": (r["full"] or "")[:300],
            }
            for r in sorted(windowed, key=lambda x: x["date"])
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Dreaming-loop evidence scanner")
    ap.add_argument("--loop-root", required=True,
                    help="absolute path to loopprojects (the loop*/ dirs live here)")
    ap.add_argument("--extra", help="extra corpus file (loop12/observed-runs.md)")
    ap.add_argument("--from", dest="after", default="2000-01-01",
                    help="scan records dated strictly after this (last dreaming date)")
    ap.add_argument("--until", default="2999-12-31", help="scan records dated up to this")
    ap.add_argument("--json", action="store_true", help="emit JSON to stdout")
    ap.add_argument("--self-test", action="store_true",
                    help="print every parsed record (debug), not just clusters")
    args = ap.parse_args()

    result = scan(Path(args.loop_root), args.after, args.until,
                  Path(args.extra) if args.extra else None)

    if args.self_test:
        for r in result["window_records"]:
            print(f'{r["date"]}  {r["file"]}:{r["line"]}  run={r["run"]}  '
                  f'{r["excerpt"][:120]!r}')
        print(f"\n-- {result['records_in_window']} windowed / "
              f"{result['candidate_records']} candidate / "
              f"{len(result['clusters'])} cluster(s) >= 2 --")
        return 0

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    # human table
    if not result["clusters"]:
        print(f"No repeated failure/correction found in the window "
              f"({result['records_in_window']} dated records).")
        return 0
    for c in result["clusters"]:
        print(f"\n[{c['count']}x] {c['signature']}")
        for r in c["records"]:
            print(f"    {r['date']}  {r['file']}:{r['line']}  "
                  f"run={r['run']}  {r['excerpt'][:120]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
