#!/usr/bin/env python3
"""loop8 loop.py - orchestrator of one daily debt-scan beat.

The deterministic brain of the loop8 daily whole-word debt-tag scan. It
runs the full six-part body in one go and then stops (a heartbeat/scheduler
wakes it again tomorrow):

    1. HOLD gate  : if the spine says NEEDS_HUMAN, record a HOLD row and stop.
    2. Isolation  : snapshot the repo at HEAD into a throwaway dir (git archive)
                    so no agent can ever touch the live tree.
    3. Ground truth: deterministic scan.py -> candidates.json (the ring that
                    never lies, loop6-style).
    4. Maker       : a fresh headless Claude implements the triage draft
                    (skills/maker-skill.md) - the ONLY file it may write.
    5. Checker     : a fresh, independent headless Claude strictly verifies the
                    draft against the files (skills/checker-skill.md).
    6. Budget      : up to MAX_ATTEMPTS maker+checker rounds; on exhaustion the
                    beat ESCALATES to NEEDS_HUMAN instead of failing silently.
    7. Commit      : on PASS the orchestrator merges the reviewed draft into
                    state.json, regenerates the progress.md spine + loop-log +
                    cost.md, and commits atomically.

Usage (canonical interpreter: C:\\Python314\\python.exe):
    python loop.py --init              # first-time scaffold of state/spine/log
    python loop.py --date 2026-09-03   # run one beat for that date
    python loop.py --reset             # human: clear NEEDS_HUMAN after fixing
    python loop.py --check             # print today's raw scan (no agents)
    python loop.py --show              # print current state summary
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

LOOP8 = Path(__file__).resolve().parent
REPO_ROOT = LOOP8.parent.parent.parent
SCAN_SCRIPT = LOOP8 / "scan.py"
RUNS_DIR = LOOP8 / "runs"
STATE_PATH = LOOP8 / "state.json"
PROGRESS_PATH = LOOP8 / "progress.md"
LOG_PATH = LOOP8 / "loop-log.md"
COST_PATH = LOOP8 / "cost.md"
USAGE_CSV = LOOP8 / "usage.csv"

REL = "loop-practice/loopprojects/loop8"   # loop8 path relative to REPO_ROOT
RUNS_REL = REL + "/runs"                   # the ONLY scratch the Maker may write

COMMIT_TRAILER = "\n\nCo-Authored-By: Claude Code <noreply@anthropic.com>\n"

# --------------------------------------------------------------------------- #
# state helpers
# --------------------------------------------------------------------------- #

INIT_STATE = {
    "project": "loop8",
    "chore": "daily whole-word debt-tag scan of this repo",
    "created": "2026-09-03",
    "run": 0,
    "last_date": None,
    "result": None,
    "reason": None,
    "state": "RUNNING",            # RUNNING | NEEDS_HUMAN
    "consecutive_failures": 0,
    "open_markers": [],            # currently-open debt: [{path,line,tags,note}]
    "reported": [],                # surfaced NEW in an earlier beat, still open
    "findings_history": [],        # compact per-beat history (newest last, cap)
    "notes": [],                   # Needs Human notes
}


def load_state() -> dict:
    if not STATE_PATH.exists():
        return json.loads(json.dumps(INIT_STATE))
    with open(STATE_PATH, encoding="utf-8") as f:
        st = json.load(f)
    for k, v in INIT_STATE.items():
        st.setdefault(k, v)
    return st


def save_state(st: dict) -> None:
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=2, ensure_ascii=False)
        f.write("\n")


# --------------------------------------------------------------------------- #
# headless Claude subprocess helper
# --------------------------------------------------------------------------- #

def find_claude() -> str:
    p = shutil.which("claude")
    if not p:
        sys.exit("loop.py: cannot find the `claude` CLI on PATH")
    return p


def run_agent(claude: str, prompt: str, out_json: Path, cwd: Path) -> dict:
    """Run one headless `claude -p` child; persist JSON + stderr to runs/.

    The child runs with cwd = the beat's working root (normally the isolated
    snapshot), so every file it reads or writes stays inside its project dir.

    Returns {ok, text, usage, err}. usage = {input, output, cache_read}.
    """
    stderr_path = out_json.with_suffix(".stderr")
    cmd = [claude, "-p", "--output-format", "json",
           "--permission-mode", "acceptEdits",
           "--no-session-persistence", prompt]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=900,
                              cwd=str(cwd))
    except subprocess.TimeoutExpired:
        return {"ok": False, "text": "", "usage": None,
                "err": "timed out after 900s"}
    out_json.write_text(proc.stdout or "", encoding="utf-8")
    stderr_path.write_text(proc.stderr or "", encoding="utf-8")
    try:
        j = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError as e:
        return {"ok": False, "text": proc.stdout, "usage": None,
                "err": f"child did not return JSON: {e}"}
    text = j.get("result") or ""
    usage = j.get("usage") or {}
    return {
        "ok": not j.get("is_error", False) and bool(text),
        "text": text,
        "usage": {
            "input": usage.get("input_tokens", 0),
            "output": usage.get("output_tokens", 0),
            "cache_read": usage.get("cache_read_input_tokens", 0),
        },
        "err": "",
    }


# --------------------------------------------------------------------------- #
# git / snapshot / manifest helpers
# --------------------------------------------------------------------------- #

def git(args: list[str], cwd: Path = REPO_ROOT) -> str:
    r = subprocess.run(["git", "-C", str(cwd)] + args,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return (r.stdout or "").strip()


def make_snapshot() -> Path:
    """Materialise HEAD into a throwaway dir; return that dir's parent.

    The snapshot lives under LOOP8/.loop8-beats/ (git-ignored) rather than
    %TEMP%: a headless `claude -p` child run in an untrusted temp folder stalls
    on the folder-trust prompt, while a path inside the already-trusted repo
    tree starts immediately. It is still fully isolated: it is never tracked,
    the agents only ever run there, and only the reviewed draft is copied out.
    """
    beats_root = LOOP8 / ".loop8-beats"
    beats_root.mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="beat-", dir=str(beats_root)))
    snap = tmp / "snapshot"
    snap.mkdir()
    arc = subprocess.run(["git", "-C", str(REPO_ROOT), "archive", "--format=tar",
                          "HEAD"], capture_output=True)
    if arc.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit("loop.py: git archive HEAD failed: "
                 + arc.stderr.decode("utf-8", "replace"))
    with tarfile.open(fileobj=io.BytesIO(arc.stdout), mode="r:") as tar:
        tar.extractall(snap)
    return tmp


def _hash_files(root: Path) -> dict:
    """relpath -> sha1 for every file under root, ignoring the loop8 runs dir."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", "__pycache__", ".loop8",
                                    ".loop8-beats")]
        for name in filenames:
            p = Path(dirpath) / name
            rel = str(p.relative_to(root)).replace("\\", "/")
            if rel == RUNS_REL or rel.startswith(RUNS_REL + "/"):
                continue
            try:
                out[rel] = hashlib.sha1(p.read_bytes()).hexdigest()
            except OSError:
                continue
    return out


def source_diffs(snap: Path, baseline: dict) -> list:
    """Relpaths that changed since baseline (the loop8 runs dir is ignored)."""
    after = _hash_files(snap)
    return [rel for rel in set(baseline) | set(after)
            if baseline.get(rel) != after.get(rel)]


# --------------------------------------------------------------------------- #
# scan / cost plumbing
# --------------------------------------------------------------------------- #

def run_scan(repo: Path) -> dict:
    r = subprocess.run([sys.executable, str(SCAN_SCRIPT), "--repo-root",
                        str(repo), "--json"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    if r.returncode != 0:
        raise RuntimeError("scan.py failed: " + (r.stderr or r.stdout)[:400])
    return json.loads(r.stdout)


def marker_key(m: dict) -> str:
    return f"{m['path']}:{m['line']}"


def record_usage(csv_path: Path, run: int, date: str, phase: str, attempt: int,
                 usage, result: str) -> None:
    if not csv_path.exists():
        csv_path.write_text(
            "run,date,phase,attempt,input_tokens,output_tokens,cache_read,result\n",
            encoding="utf-8")
    u = usage or {}
    with open(csv_path, "a", encoding="utf-8") as f:
        f.write(f"{run},{date},{phase},{attempt},{u.get('input', 0)},"
                f"{u.get('output', 0)},{u.get('cache_read', 0)},{result}\n")


# --------------------------------------------------------------------------- #
# progress.md / loop-log.md / cost.md generation
# --------------------------------------------------------------------------- #

def build_progress(st: dict) -> str:
    lines = [
        "# Progress — Project 8 (Capstone: Your Own Daily Loop)",
        "",
        "A **daily whole-word debt-tag scan** over this repo. Each beat: a",
        "fresh engine snapshot-isolates the repo, the Maker drafts a triage",
        "report from the deterministic scan, a strict Checker verifies it, and",
        "only on PASS the reviewed findings land here. This file is *generated*",
        "by `loop.py` from `state.json`; do not hand-edit it.",
        "",
        "## Last Run",
        "",
        f"- **Run:** {st['run']}",
        f"- **When:** {st['last_date'] or '—'}",
        f"- **Result:** {st['result'] or '—'}",
        f"- **Reason:** {st['reason'] or '—'}",
        f"- **Consecutive failures:** {st['consecutive_failures']}",
        f"- **State:** {st['state']} _(RUNNING | NEEDS_HUMAN)_",
        "",
        "## Findings",
        "",
    ]
    if not st["findings_history"]:
        lines.append("_(No beat has run yet. `python loop.py --date YYYY-MM-DD`"
                     " runs the first one.)_")
        lines.append("")
    for h in st["findings_history"][-7:]:
        new = h.get("new", [])
        res = h.get("resolved", [])
        lines += [
            f"### {h['date']} — {h['result']} (run {h['run']})",
            "",
            f"New: {len(new)} · Existing open: {h.get('existing_count', 0)} ·"
            f" Resolved: {len(res)}",
            "",
        ]
        if new:
            for m in new:
                lines.append(f"- NEW `{marker_key(m)}` [{'/'.join(m['tags'])}]"
                             f" — {m.get('note', '')}")
            lines.append("")
        else:
            lines += ["- No new debt markers.", ""]
        if res:
            lines += ["- Resolved:", ""]
            for r_ in res:
                lines.append(f"  - `{r_}`")
            lines.append("")

    lines += ["## Already Reported", "",
              "_(Markers first surfaced as NEW in an earlier beat and still"
              " open, so they aren't re-announced.)_", ""]
    if not st["reported"]:
        lines.append("- _none — no open markers have ever been reported._")
    for m in st["reported"]:
        lines.append(f"- `{marker_key(m)}` [{'/'.join(m['tags'])}] — first seen"
                     f" {m['first_seen']} — {m.get('note', '')}")
    lines += ["", "## Needs Human", ""]
    if not st["notes"]:
        lines.append("_(Nothing needs a human right now. This section stays"
                     " empty only while the loop is healthy.)_")
    for n in st["notes"]:
        lines += [
            f"- **{n['date']}** — **What failed:** {n['what']}",
            f"  **Since when:** {n['since']}.",
            f"  **Attempts:** {n['attempts']}.",
            f"  **Loop action:** {n['action']}",
            f"  **First thing to check:** {n['check']}",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def write_spine(st: dict) -> None:
    PROGRESS_PATH.write_text(build_progress(st), encoding="utf-8")


def append_log(run, date, result, note) -> None:
    header = "| Run | Date | Result | Notes |\n|-----|------|--------|-------|\n"
    if not LOG_PATH.exists():
        LOG_PATH.write_text("# loop8 — daily debt scan: run log\n\n" + header,
                            encoding="utf-8")
    note_s = str(note).replace("|", "/").replace("\n", " ")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"| {run} | {date} | {result} | {note_s} |\n")


def build_cost() -> str:
    rows = []
    if USAGE_CSV.exists():
        data = USAGE_CSV.read_text(encoding="utf-8").splitlines()
        rows = [line.split(",") for line in data[1:] if line.strip()]
    lines = [
        "# Cost of the loop8 daily debt scan — measured, not guessed",
        "",
        "Each beat runs fresh headless Claude agents (Maker + Checker), each a",
        "real `claude -p` subprocess whose token usage is captured from the run",
        "JSON (see `runs/`). Numbers below are **measured**, not modelled.",
        "",
    ]
    if not rows:
        lines += ["_No beats have run yet. Measured rows appear after the first",
                  "beat._", ""]
        COST_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        return

    by_run = {}
    for r in rows:
        by_run.setdefault(r[0], []).append(r)

    lines += ["## Measured tokens per beat", "",
              "| Beat | Date | Input | Output | Cache-read | Agent runs |",
              "|------|------|-------|--------|------------|------------|"]
    tot_in = tot_out = 0
    n_beats = len(by_run)
    for run in sorted(by_run, key=int):
        rs = by_run[run]
        date = rs[0][1]
        inp = sum(int(r_[4]) for r_ in rs)
        out = sum(int(r_[5]) for r_ in rs)
        cache = sum(int(r_[6]) for r_ in rs)
        tot_in += inp
        tot_out += out
        lines.append(f"| {run} | {date} | {inp:,} | {out:,} | {cache:,} |"
                     f" {len(rs)} |")
    mean_in = tot_in / n_beats
    mean_out = tot_out / n_beats
    lines += [
        "",
        f"Totals over {n_beats} beat(s): **{tot_in:,} input + {tot_out:,} output"
        f" tokens**; mean ~{mean_in:,.0f} input per beat.",
        "",
        "## Monthly projection (once per day, 30 runs)",
        "",
        f"- Input: {mean_in:,.0f} × 30 ≈ **{mean_in*30:,.0f} tokens/month**",
        f"- Output: {mean_out:,.0f} × 30 ≈ **{mean_out*30:,.0f} tokens/month**",
        "",
        "Dollars = `tokens × provider $/MTok / 1,000,000`. The dominant term is",
        "the per-invocation harness overhead paid for every agent run, not the",
        "loop's own content. Reference rates (illustrative only):",
        "",
        "| Rate tier | Input $/MTok | Output $/MTok | ~Cost/month |",
        "|-----------|--------------|---------------|-------------|",
        "| Haiku 4.5-tier | $1.00 | $5.00 | ~$0.30–0.60 |",
        "| Sonnet 5-tier | $2.00 | $10.00 | ~$0.60–1.20 |",
        "| Opus 5-tier | $5.00 | $25.00 | ~$1.50–3.00 |",
        "",
        "Two things to *not* trust: (1) `total_cost_usd` in the run JSON is a",
        "guess — the harness reports it with `costBasis: unknown`; the token",
        "counts are the reliable measurement. (2) This loop runs through this",
        "machine's configured backend"
        f" (`ANTHROPIC_MODEL={os.environ.get('ANTHROPIC_MODEL', '?')}`), not"
        " Anthropic's first-party API — substitute the provider's $/MTok.",
        "",
    ]
    COST_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# beat state transitions
# --------------------------------------------------------------------------- #

def merge_success(st: dict, date: str, draft: dict) -> None:
    """Fold a PASSed draft into machine state (called only on a PASS)."""
    st["run"] += 1
    st["last_date"] = date
    st["result"] = "SUCCESS"
    st["reason"] = "checker PASS — reviewed draft accepted"
    st["consecutive_failures"] = 0
    st["state"] = "RUNNING"

    real = draft.get("real", [])
    open_keys = {marker_key(m) for m in st["open_markers"]}
    new_here = [m for m in real if marker_key(m) not in open_keys]
    still_keys = {marker_key(m) for m in real}
    resolved = sorted(open_keys - still_keys)

    st["open_markers"] = [dict(m) for m in real]
    kept = [m for m in st["reported"] if marker_key(m) in still_keys]
    for m in new_here:
        if marker_key(m) not in {marker_key(x) for x in kept}:
            kept.append({**dict(m), "first_seen": date})
    st["reported"] = kept

    st["findings_history"].append({
        "date": date, "run": st["run"], "result": "SUCCESS",
        "new": [dict(m) for m in new_here],
        "existing_count": len(real) - len(new_here),
        "resolved": resolved,
    })
    st["findings_history"] = st["findings_history"][-60:]


def do_escalate(st: dict, date: str, why: str, attempts: int,
                first_check: str) -> None:
    st["run"] += 1
    st["last_date"] = date
    st["result"] = "ESCALATED"
    st["reason"] = why
    st["consecutive_failures"] = st["consecutive_failures"] + 1
    st["state"] = "NEEDS_HUMAN"
    st["notes"].append({
        "date": date,
        "what": why,
        "since": date,
        "attempts": f"{attempts} maker+checker attempt(s) in this beat",
        "action": "stopped retrying — State set to NEEDS_HUMAN; later beats HOLD",
        "check": first_check,
    })
    st["notes"] = st["notes"][-20:]


# --------------------------------------------------------------------------- #
# agent wake prompts
# --------------------------------------------------------------------------- #

def prompt_for(date: str, run: int, tag: str, runs_path: Path,
               work_root: Path) -> str:
    cand = runs_path / f"candidates-{run}.json"
    draft = runs_path / f"draft-{run}.json"
    loop8_wk = work_root / REL.replace("/", os.sep)
    state = loop8_wk / "state.json"
    skill = loop8_wk / "skills"
    maker_skill = skill / "maker-skill.md"
    checker_skill = skill / "checker-skill.md"
    if tag == "maker":
        return (
            f"You are the Maker of the loop8 daily debt-scan loop, woken headless "
            f"for one beat. Read and follow EXACTLY the contract at:\n{maker_skill}"
            f"\n\nYour inputs:\n  DATE={date}\n  RUN={run}\n  STATE={state}\n"
            f"  SCAN_CANDIDATES={cand}\n  DRAFT_OUT={draft}\n\n"
            f"Read STATE and SCAN_CANDIDATES, triage every candidate, write "
            f"DRAFT_OUT exactly per the skill, then reply one line: "
            f"MAKER DRAFT {run} COMPLETE"
        )
    return (
        f"You are the Checker of the loop8 daily debt-scan loop, woken headless "
        f"for one beat, AFTER the Maker. You are the strict independent reviewer. "
        f"Read and follow EXACTLY the contract at:\n{checker_skill}\n\n"
        f"Your inputs:\n  DATE={date}\n  RUN={run}\n  STATE={state}\n"
        f"  DRAFT={draft}\n  SCAN_CANDIDATES={cand}\n  REPO_ROOT={work_root}\n\n"
        f"Verify the draft strictly against the files, then reply first line "
        f"exactly VERDICT: PASS or VERDICT: FAIL, then your reasons."
    )


# --------------------------------------------------------------------------- #
# beat body
# --------------------------------------------------------------------------- #

def beat(args) -> int:
    claude = find_claude()
    date = args.date
    max_attempts = args.max_attempts
    st = load_state()

    if st["state"] == "NEEDS_HUMAN":
        print(f"BEAT HOLD — {st['result']} on {st['last_date']}, waiting on a "
              f"human. Fix the cause, then run `python loop.py --reset`.")
        append_log("—", date, "HOLD", "escalated, waiting on human")
        return 0

    if st["last_date"] == date and st["result"] == "SUCCESS":
        print(f"BEAT SKIP — a SUCCESS beat for {date} already ran.")
        return 0

    run = st["run"] + 1
    tmp = None
    try:
        # ---- isolation: agents work on a throwaway snapshot of HEAD --------
        if args.isolation:
            tmp = make_snapshot()
            work_root = tmp / "snapshot"
        else:
            work_root = REPO_ROOT
        runs_path = work_root / REL.replace("/", os.sep) / "runs"
        runs_path.mkdir(parents=True, exist_ok=True)
        real_runs = RUNS_DIR
        real_runs.mkdir(parents=True, exist_ok=True)

        cand = runs_path / f"candidates-{run}.json"
        cand.write_text(json.dumps(run_scan(work_root), indent=2),
                        encoding="utf-8")
        baseline = _hash_files(work_root) if args.isolation else None
        n_cand = len(json.loads(cand.read_text(encoding="utf-8"))["lines"])
        print(f"beat {run} @ {date} — scan found {n_cand} candidate line(s)")

        outcome = None          # SUCCESS | ESCALATE
        feedback = ""
        for attempt in range(1, max_attempts + 1):
            draft = runs_path / f"draft-{run}.json"

            # ---------- MAKER ----------
            p_m = prompt_for(date, run, "maker", runs_path, work_root)
            if attempt > 1:
                p_m += (f"\n\nYour previous draft was FAILed by the Checker. Read "
                        f"{draft}, fix EVERY discrepancy in the reasons below, and "
                        f"overwrite DRAFT_OUT. Recheck the whole candidate list — "
                        f"do not only patch the flagged lines.\nCHECKER REASONS:\n"
                        + feedback)
            r_m = run_agent(claude, p_m, real_runs /
                            f"beat-{run}.maker.{attempt}.json", work_root)
            record_usage(USAGE_CSV, run, date, "maker", attempt, r_m["usage"],
                         "OK" if r_m["ok"] else "ERROR")
            if not r_m["ok"]:
                feedback = (r_m.get("err") or r_m["text"])[-600:]
                print(f"  attempt {attempt}: maker errored — {feedback[:100]}")
                if attempt == max_attempts:
                    outcome = "ESCALATE"
                continue
            try:
                draft_doc = json.loads(draft.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, FileNotFoundError) as e:
                feedback = f"maker wrote no valid draft JSON: {e}"
                print(f"  attempt {attempt}: {feedback}")
                if attempt == max_attempts:
                    outcome = "ESCALATE"
                continue

            # ---- hygiene: the maker must not have touched any source --------
            if baseline is not None:
                diffs = source_diffs(work_root, baseline)
                if diffs:
                    why = (f"Maker modified source file(s) in the snapshot: "
                           f"{diffs[:5]} — it wrote outside its draft. Beat "
                           f"aborted for safety.")
                    print("  SAFETY STOP — " + why)
                    do_escalate(st, date, why, attempt,
                                "inspect runs/beat-*.maker.*.json + .stderr")
                    save_state(st)
                    write_spine(st)
                    append_log(run, date, "ESCALATED",
                               "maker modified sources — safety stop")
                    return 3

            # ---------- CHECKER ----------
            p_c = prompt_for(date, run, "checker", runs_path, work_root)
            r_c = run_agent(claude, p_c, real_runs /
                            f"beat-{run}.checker.{attempt}.json", work_root)
            m = re.search(r"VERDICT:\s*(PASS|FAIL)", r_c["text"])
            verdict = m.group(1) if m else "FAIL"
            record_usage(USAGE_CSV, run, date, "checker", attempt, r_c["usage"],
                         verdict)
            if verdict == "PASS":
                print(f"  attempt {attempt}: checker PASS")
                merge_success(st, date, draft_doc)
                outcome = "SUCCESS"
                break
            feedback = (r_c["text"] or "no reasons given")[-1500:]
            print(f"  attempt {attempt}: checker FAIL — "
                  f"{len(draft_doc.get('real', []))} real marker(s) disputed")

        if outcome is None:
            outcome = "ESCALATE"

        if outcome == "ESCALATE":
            why = (f"Maker and Checker never agreed after {max_attempts} "
                   f"attempt(s). Last failure: {feedback[:400] or 'unknown'}")
            do_escalate(st, date, why, max_attempts,
                        "read runs/beat-*.checker.*.json for the Checker's reasons")
            print(f"  → ESCALATED: {why[:160]}")

        save_state(st)
        write_spine(st)
        if outcome == "SUCCESS":
            h = [x for x in st["findings_history"] if x["run"] == st["run"]][0]
            append_log(run, date, "SUCCESS",
                       f"checker PASS — {len(h['new'])} new marker(s), "
                       f"{len(st['open_markers'])} open, "
                       f"{len(h['resolved'])} resolved")
        else:
            append_log(run, date, "ESCALATED", "maker/checker never agreed")

        # copy the beat artifacts back to the live tree for the record
        if args.isolation:
            for name in (f"candidates-{run}.json", f"draft-{run}.json"):
                src = runs_path / name
                if src.exists():
                    shutil.copyfile(src, real_runs / name)

        build_cost()
        print(f"RUN {run} COMPLETE — {outcome}")
        return 0 if outcome == "SUCCESS" else 2
    finally:
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def commit_beat(message: str) -> None:
    """Atomically commit the loop8 folder's beat output."""
    subprocess.run(["git", "-C", str(REPO_ROOT), "add", "--", REL],
                   check=False)
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "diff", "--cached",
                        "--quiet"], check=False)
    if r.returncode != 0:
        subprocess.run(["git", "-C", str(REPO_ROOT), "commit", "-m",
                        message + COMMIT_TRAILER], check=False)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="loop8 daily debt-scan orchestrator")
    ap.add_argument("--date", default=_dt.date.today().isoformat())
    ap.add_argument("--max-attempts", type=int, default=3)
    ap.add_argument("--isolation", action="store_true", default=True,
                    help="run Maker/Checker in a throwaway git-archive snapshot")
    ap.add_argument("--no-isolation", dest="isolation", action="store_false")
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--no-commit", dest="commit", action="store_false",
                    default=True, help="skip the atomic git commit")
    a = ap.parse_args(argv)

    if a.init:
        if not STATE_PATH.exists():
            save_state(INIT_STATE)
        st = load_state()
        write_spine(st)
        if not LOG_PATH.exists():
            append_log("—", "—", "—", "scaffold created")
        build_cost()
        print("loop8 initialised: state.json, progress.md, loop-log.md, cost.md")
        return 0

    if a.reset:
        st = load_state()
        st["state"] = "RUNNING"
        st["result"] = None
        st["reason"] = None
        st["consecutive_failures"] = 0
        save_state(st)
        write_spine(st)
        print("State reset to RUNNING. Run a beat with --date to resume.")
        return 0

    if a.check:
        doc = run_scan(REPO_ROOT)
        for ln in doc["lines"]:
            print(f"{ln['path']}:{ln['line']}  [{'/'.join(ln['tags'])}]  "
                  f"{ln['text']!r}")
        print(f"\n{len(doc['lines'])} candidate line(s) in the live tree.")
        return 0

    if a.show:
        st = load_state()
        print(json.dumps(st, indent=2, ensure_ascii=False))
        return 0

    rc = beat(a)
    if a.commit and rc in (0, 2):
        outcome = "SUCCESS" if rc == 0 else "ESCALATED"
        commit_beat(f"loop8 beat: {outcome}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
