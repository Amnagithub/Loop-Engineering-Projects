#!/usr/bin/env python3
"""loop8 scan.py - the deterministic ground-truth ring of the daily debt scan.

Finds every line under the repo that contains a *whole-word* debt tag
(``TODO`` / ``FIXME`` / ``HACK`` / ``XXX``). It does NOT decide whether a hit is
real debt or prose noise - that triage belongs to the Maker agent
(skills/maker-skill.md), and the Checker agent re-runs this scan independently
(skills/checker-skill.md) to verify the Maker neither invented nor missed a
marker. This scan is what loop6 would call the ring that "never lies".

Deliberate scope choices:
  * Only text files (see TEXT_EXTENSIONS) are scanned.
  * Whole-word matching excludes plurals ("TODOs", "FIXMEs") and words that
    merely *contain* a tag (e.g. "fixme-not"). A boundary before AND after the
    tag is required.
  * Loop-generated bookkeeping is not scanned: `progress.md`, `loop-log.md`,
    `cost.md`, `state.json`, `usage.csv`, and any directory named `runs/`. The
    loop does not report debt in its own logs, and doing so would create a
    perpetual self-referential candidate.

Run:
    python scan.py --repo-root <path>            # human-readable table
    python scan.py --repo-root <path> --json     # machine-readable (used by the loop)
    python scan.py --repo-root <path> --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TAGS = ("TODO", "FIXME", "HACK", "XXX")
TAG_RE = re.compile(r"\b(?:TODO|FIXME|HACK|XXX)\b")

TEXT_EXTENSIONS = {
    ".py", ".pyw", ".md", ".markdown", ".txt", ".rst", ".yml", ".yaml",
    ".json", ".sh", ".ps1", ".bat", ".cmd", ".html", ".htm", ".css",
    ".js", ".mjs", ".ts", ".jsx", ".tsx", ".toml", ".ini", ".cfg", ".svg",
}

SKIP_DIR_NAMES = {".git", "__pycache__", "node_modules", "venv", ".venv",
                  ".idea", ".vscode", "runs", ".hg", ".svn"}

# Loop-generated bookkeeping files are not source of truth for debt.
SKIP_FILE_NAMES = {"progress.md", "loop-log.md", "cost.md", "state.json",
                   "usage.csv", "README.md"}


def _iter_text_files(root: Path):
    for dirpath, dirnames, filenames in os_walk_no_skip(root):
        for name in sorted(filenames):
            if name in SKIP_FILE_NAMES:
                continue
            p = dirpath / name
            if p.suffix.lower() in TEXT_EXTENSIONS:
                yield p


def os_walk_no_skip(root: Path):
    """os.walk that prunes SKIP_DIR_NAMES at every level."""
    import os
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in SKIP_DIR_NAMES and not d.startswith(".loop8")]
        yield Path(dirpath), dirnames, filenames


def scan_tree(repo_root: Path):
    """Return a list of candidate lines: one dict per matching line."""
    root = Path(repo_root).resolve()
    lines: list[dict] = []
    for path in _iter_text_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        for lineno, raw in enumerate(text.splitlines(), start=1):
            m = TAG_RE.search(raw)
            if not m:
                continue
            tags = list(dict.fromkeys(TAG_RE.findall(raw)))
            lines.append({
                "path": rel,
                "line": lineno,
                "tags": tags,
                "text": raw.rstrip("\r\n"),
            })
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="loop8 deterministic debt scan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)

    root = Path(a.repo_root).resolve()
    if not root.is_dir():
        print(f"scan error: not a directory: {root}", file=sys.stderr)
        return 2

    lines = scan_tree(root)
    import datetime
    doc = {
        "repo_root": str(root),
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "count": len(lines),
        "lines": lines,
    }

    if a.json:
        print(json.dumps(doc, indent=2))
        return 0

    print(f"# loop8 debt scan — {root.name}  ({doc['generated']})")
    print(f"Candidate lines containing a whole-word tag: {len(lines)}\n")
    for ln in lines:
        print(f"{ln['path']}:{ln['line']}  [{'/'.join(ln['tags'])}]  {ln['text']!r}")

    if a.self_test:
        ok = all(isinstance(ln["line"], int) and ln["path"] and ln["tags"]
                 and "\n" not in ln["text"] for ln in lines)
        print(f"\nself-test: {'PASS' if ok else 'FAIL'} "
              f"({len(lines)} candidate lines, structurally valid)"
              if ok else "\nself-test: FAIL")
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
