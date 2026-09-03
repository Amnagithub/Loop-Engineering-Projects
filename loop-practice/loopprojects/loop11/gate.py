#!/usr/bin/env python3
"""Project 11 - The Two-Routine Gate (Human Gate) engine + local API.

Two routines, one human in the middle.

  Routine A (DRAFT ONLY)   -> writes a reviewable plan (a proposed annotated
                              git tag on a pinned commit) and seals state to
                              AWAITING_REVIEW. It performs NO git mutation.
  HUMAN                    -> reviews the plan, then runs `approve`, which
                              mints a one-time approval token into a
                              GITIGNORED file (.approval-token). The token
                              never exists in the repo, so no Routine clone
                              can ever self-approve (the loop10 lesson).
  Routine B (ACTION ONLY)  -> an API-triggered step. It refuses unless the
                              state is APPROVED, the caller proves the token,
                              and the plan file still hashes to the value the
                              human approved. Only then does it run the ONE
                              reviewed command (create the annotated tag).

Every event is appended to ledger.jsonl - the transcript of the gate. A 200
from /fire is NOT the proof; the ledger line + the git tag object are.

Subcommands (run from anywhere; the script finds the repo root via git):
  python gate.py draft              Routine A stand-in: author + seal a plan
  python gate.py seal <plan-file>   seal an already-authored plan (real Routine A)
  python gate.py approve            HUMAN step: mint token, phase -> APPROVED
  python gate.py fire <sha> --token <tok>   Routine B: verify, then act
  python gate.py serve              local API: GET /status, POST /fire  (curl)
  python gate.py status             print the gate state
  python gate.py reset              back to PENDING (deletes the token file)
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import http.server
import json
import os
import secrets
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

GATE = Path(__file__).resolve().parent            # .../loop11
STATE_FILE = GATE / "state.json"
LEDGER_FILE = GATE / "ledger.jsonl"
TOKEN_FILE = GATE / ".approval-token"             # GITIGNORED - never committed
RUNS_DIR = GATE / "runs"
TAG_PREFIX = "loop11/gate-"
META_BEGIN = "<!-- gate-metadata -->"
META_END = "<!-- /gate-metadata -->"
PY = sys.executable


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    out = subprocess.run(
        ["git", "-C", str(GATE), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    )
    return Path(out.stdout.strip())


def rel_to_root(path: Path) -> str:
    return path.resolve().relative_to(repo_root()).as_posix()


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo_root()), *args],
                          capture_output=True, text=True)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def token_fp(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()[:12]


def load_state() -> dict:
    if not STATE_FILE.exists():
        return _blank_state()
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def _blank_state() -> dict:
    return {
        "version": 1,
        "phase": "PENDING",            # PENDING -> AWAITING_REVIEW -> APPROVED -> DONE
        "run": None,
        "plan_path": None,             # relative to repo root, e.g. loop11/runs/01/plan.md
        "plan_sha256": None,
        "tag": None,
        "target_commit": None,
        "created_at": None,
        "approved_at": None,
        "fired_at": None,
        "fired_token_fp": None,
    }


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def log_event(**fields) -> None:
    """Append one line to ledger.jsonl - the append-only transcript."""
    line = {"t": now_iso(), **fields}
    with LEDGER_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(line, ensure_ascii=False) + "\n")


def next_run_label() -> str:
    """Next zero-padded run number by scanning runs/ (01, 02, ...)."""
    if not RUNS_DIR.exists():
        return "01"
    existing = [int(p.name) for p in RUNS_DIR.iterdir() if p.is_dir()
                and p.name.isdigit()]
    return f"{max(existing) + 1:02d}" if existing else "01"


def read_token() -> str | None:
    if not TOKEN_FILE.exists():
        return None
    val = TOKEN_FILE.read_text(encoding="utf-8").strip()
    return val or None


def write_token(token: str) -> None:
    TOKEN_FILE.write_text(token + "\n", encoding="utf-8")


def clear_token() -> None:
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()


def require_phase(state: dict, *phases: str) -> None:
    if state["phase"] not in phases:
        sys.exit(f"REFUSED: phase is {state['phase']!r}, expected "
                 f"{'/'.join(phases)}.")


def parse_plan_meta(plan_text: str) -> dict:
    """Read the machine-readable JSON block a plan must carry."""
    begin = plan_text.find(META_BEGIN)
    end = plan_text.find(META_END)
    if begin < 0 or end < 0 or end <= begin:
        raise ValueError("plan.md has no gate-metadata block")
    body = plan_text[begin + len(META_BEGIN):end].strip()
    meta = json.loads(body)
    for key in ("tag", "target", "message"):
        if key not in meta or not meta[key]:
            raise ValueError(f"plan.md metadata is missing '{key}'")
    return meta


def current_head() -> str:
    proc = git("rev-parse", "HEAD")
    if proc.returncode != 0:
        sys.exit("REFUSED: cannot read HEAD of the repo - stop and report.")
    return proc.stdout.strip()


def head_subject() -> str:
    proc = git("log", "-1", "--format=%s")
    return proc.stdout.strip() or "(no subject)"


# --------------------------------------------------------------------------- #
# the plan file (what the human reviews)
# --------------------------------------------------------------------------- #

def _message_for(run: str, head: str, subject: str) -> str:
    title = f"{TAG_PREFIX}{run}: approve Project 11 gate run {run}"
    body = (
        f"This annotated tag marks commit {head[:12]} ({subject}) as the\n"
        "release point for Project 11 (Two-Routine Gate). Routine A drafted\n"
        "this plan; a human reviewed it and fired Routine B to create the tag.\n"
        "The tag is the machine-readable proof the gate held: Routine B ran\n"
        "exactly once, only after human approval."
    )
    return title + "\n\n" + body


def _render_plan(run: str, head: str, subject: str, message: str) -> str:
    tag = f"{TAG_PREFIX}{run}"
    meta = {"tag": tag, "target": head, "message": message}
    meta_json = json.dumps(meta, ensure_ascii=False, indent=2)
    return f"""# Gate plan - run {run}   (HUMAN REVIEW REQUIRED - nothing has run yet)

Prepared by: Routine A (draft only) at {now_iso()}
Repo: {rel_to_root(GATE)}
Target commit: {head}  ({subject})
Phase: AWAITING_REVIEW

{META_BEGIN}
{meta_json}
{META_END}

## Proposed action (ONE irreversible step)

Create the annotated git tag `{tag}` at commit `{head}`:

    git tag -a {tag} {head} -m "<message below>"

## Message Routine B will attach

{message}

## Note to the human

I, Routine A, can only draft. I did NOT create any tag, branch, or commit,
and I did not push. Please review this plan. If you approve:

    python loop-practice/loopprojects/loop11/gate.py approve

That prints a one-time approval token and the exact curl that fires
Routine B. The gate refuses to fire until you approve, and it only ever
creates the tag described on THIS page.
"""


# --------------------------------------------------------------------------- #
# Routine A (draft only)
# --------------------------------------------------------------------------- #

def cmd_draft() -> int:
    """Routine A stand-in: compose a plan from repo facts, seal it."""
    state = load_state()
    if state["phase"] in ("AWAITING_REVIEW", "APPROVED"):
        sys.exit("REFUSED: a plan is already out for review. Finish or reset "
                 "first (python gate.py reset).")
    run = next_run_label()
    head = current_head()
    subject = head_subject()
    message = _message_for(run, head, subject)
    run_dir = RUNS_DIR / run
    run_dir.mkdir(parents=True, exist_ok=True)
    plan_path = run_dir / "plan.md"
    plan_path.write_text(_render_plan(run, head, subject, message),
                         encoding="utf-8")
    seal(run_dir, plan_path)
    return 0


def cmd_seal(plan_file: str) -> int:
    """Register a plan authored by a REAL Routine A (headless run)."""
    src = Path(plan_file)
    if not src.is_file():
        sys.exit(f"REFUSED: no such plan file: {plan_file}")
    state = load_state()
    if state["phase"] in ("AWAITING_REVIEW", "APPROVED"):
        sys.exit("REFUSED: a plan is already out for review. Finish or reset "
                 "first (python gate.py reset).")
    # validate it before it becomes the reviewable artifact
    parse_plan_meta(src.read_text(encoding="utf-8"))
    run = next_run_label()
    run_dir = RUNS_DIR / run
    run_dir.mkdir(parents=True, exist_ok=True)
    plan_path = run_dir / "plan.md"
    shutil.copy2(src, plan_path)
    seal(run_dir, plan_path)
    return 0


def seal(run_dir: Path, plan_path: Path) -> None:
    """Compute the hash, flip state to AWAITING_REVIEW, log A's draft."""
    plan_text = plan_path.read_text(encoding="utf-8")
    meta = parse_plan_meta(plan_text)
    run = run_dir.name
    state = {
        **_blank_state(),
        "phase": "AWAITING_REVIEW",
        "run": run,
        "plan_path": rel_to_root(plan_path),
        "plan_sha256": sha256_file(plan_path),
        "tag": meta["tag"],
        "target_commit": meta["target"],
        "created_at": now_iso(),
    }
    save_state(state)
    log_event(
        event="A_drafted", run=run, actor="routine-a",
        plan_path=rel_to_root(plan_path),
        plan_sha256=state["plan_sha256"],
        tag=meta["tag"], target_commit=meta["target"],
        phase="AWAITING_REVIEW",
    )
    print("==== Routine A (draft only) ====")
    print(f"plan written:   {rel_to_root(plan_path)}")
    print(f"proposed tag:   {meta['tag']}  ->  commit {meta['target'][:12]}")
    print(f"plan sha256:    {state['plan_sha256']}")
    print(f"phase:          AWAITING_REVIEW  (Routine B has NOT been fired)")
    print()
    print("NOTE TO THE HUMAN: review the plan above. Nothing irreversible has")
    print("happened. When ready:  python loop-practice/loopprojects/loop11/gate.py approve")


# --------------------------------------------------------------------------- #
# HUMAN step: approve
# --------------------------------------------------------------------------- #

def cmd_approve() -> int:
    """The ONLY way phase becomes APPROVED, and the ONLY place the one-time
    approval token is minted. The token is written to a gitignored file, so a
    Routine clone (which only has committed files) can never see it."""
    state = load_state()
    require_phase(state, "AWAITING_REVIEW")
    plan_abs = repo_root() / state["plan_path"]
    if not plan_abs.is_file():
        sys.exit(f"REFUSED: approved plan {state['plan_path']} is missing.")
    digest = sha256_file(plan_abs)
    # Bind THIS exact plan content: if the human edited the plan during
    # review, re-hash so Routine B later executes the version they reviewed.
    state["phase"] = "APPROVED"
    state["plan_sha256"] = digest
    state["approved_at"] = now_iso()
    save_state(state)

    token = secrets.token_hex(16)
    write_token(token)
    log_event(
        event="human_approved", run=state["run"], actor="human",
        plan_sha256=digest, token_fp=token_fp(token),
        phase="APPROVED",
    )
    print("==== Human approval recorded ====")
    print(f"approved plan:  {state['plan_path']}  (sha256 {digest})")
    print(f"phase:          APPROVED")
    print()
    print("ONE-TIME APPROVAL TOKEN (keep it secret, it is your signature):")
    print(f"    {token}")
    print()
    print("Fire Routine B now with curl (this exact request):")
    print()
    print(f'    curl -s -X POST http://127.0.0.1:8787/fire \\')
    print(f"        -H 'Content-Type: application/json' \\")
    print(f'        -d \'{{"token":"{token}","plan_sha256":"{digest}"}}\'')
    print()
    print("(If the API server is not running, the equivalent CLI is:")
    print(f'  python loop-practice/loopprojects/loop11/gate.py fire {digest} --token {token})')
    return 0


# --------------------------------------------------------------------------- #
# Routine B (action only)
# --------------------------------------------------------------------------- #

def do_fire(claimed_sha: str, token: str, channel: str = "cli") -> tuple[int, dict]:
    """Routine B's single code path - CLI and POST /fire both land here.

    Returns (http-ish status, result dict). Every attempt is logged, success
    or refusal, so ledger.jsonl is the transcript of the gate.
    """
    state = load_state()
    run = state["run"]

    def refuse(reason: str, detail: str, code: int) -> tuple[int, dict]:
        log_event(event="B_fire_refused", run=run, channel=channel,
                  reason=reason, detail=detail, phase=state["phase"])
        return code, {"ok": False, "reason": reason, "detail": detail}

    # 1. a human must have approved (and this run must not already be done)
    if state["phase"] == "DONE":
        return refuse("already_done",
                      f"Routine B already acted for run {run} (tag "
                      f"{state['tag']}). The action happens exactly once.",
                      409)
    if state["phase"] != "APPROVED":
        return refuse("no_approval",
                      f"phase is {state['phase']!r}; a human has not approved "
                      "this plan. Routine B only acts after human approval.",
                      403)

    # 2. the caller must prove they hold the approval token. The token lives
    #    only in the gitignored .approval-token file, so a Routine clone never
    #    has it (the loop10 lesson) and nothing can self-approve.
    stored = read_token()
    if stored is None:
        return refuse("no_token",
                      ".approval-token is absent - either approval was reset, "
                      "or this is a Routine clone (the token never leaves the "
                      "human's machine).", 403)
    if not hmac.compare_digest(stored, token):
        return refuse("bad_token", "the approval token does not match the one "
                      "the human minted at approve time.", 403)

    # 3. the caller must name the exact approved plan
    if claimed_sha != state["plan_sha256"]:
        return refuse("hash_mismatch",
                      "claimed plan_sha256 does not match the approved plan. "
                      "Routine B only runs the plan the human approved.", 409)

    # 4. the plan file must still hash to the approved value (unchanged since
    #    approval - otherwise B would execute something the human never saw)
    plan_abs = repo_root() / state["plan_path"]
    if not plan_abs.is_file():
        return refuse("plan_missing", f"{state['plan_path']} is gone.", 409)
    if sha256_file(plan_abs) != state["plan_sha256"]:
        return refuse("plan_changed",
                      "plan.md changed after human approval; Routine B will "
                      "not execute an unreviewed plan.", 409)

    # 5. the action must not already exist (single-fire)
    tag = state["tag"]
    listed = git("tag", "--list", tag).stdout.strip().splitlines()
    if tag in listed:
        return refuse("already_done",
                      f"tag {tag} already exists - Routine B already acted.", 409)

    target = state["target_commit"]
    verify = git("rev-parse", "--verify", f"{target}^{{commit}}")
    if verify.returncode != 0:
        return refuse("bad_target",
                      f"commit {target[:12]} no longer resolves.", 409)

    # the ONE reviewed command, executed without a shell
    meta = parse_plan_meta(plan_abs.read_text(encoding="utf-8"))
    proc = subprocess.run(
        ["git", "-C", str(repo_root()), "tag", "-a", tag, "-m",
         meta["message"], meta["target"]],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return refuse("action_failed", proc.stderr.strip() or proc.stdout.strip(),
                      500)

    state["phase"] = "DONE"
    state["fired_at"] = now_iso()
    state["fired_token_fp"] = token_fp(token)
    save_state(state)
    log_event(
        event="B_acted", run=run, channel=channel,
        tag=tag, target_commit=target,
        token_fp=token_fp(token), phase="DONE",
    )
    print(f"==== Routine B acted ====")
    print(f"tag created:    {tag}  ->  {target}")
    print(f"token used:     {token_fp(token)} (fingerprint)")
    print(f"phase:          DONE")
    print(f"verify:         git show {tag}")
    return 200, {
        "ok": True, "tag": tag, "target_commit": target,
        "token_fp": token_fp(token), "phase": "DONE",
        "verify": f"git show {tag}",
    }


def cmd_fire(claimed_sha: str, token: str) -> int:
    code, result = do_fire(claimed_sha, token, channel="cli")
    if result["ok"]:
        return 0
    print(f"REFUSED ({code}): {result['reason']} - {result['detail']}")
    return 1


# --------------------------------------------------------------------------- #
# status / reset
# --------------------------------------------------------------------------- #

def cmd_status() -> int:
    state = load_state()
    print(json.dumps(state, indent=2))
    if state["phase"] == "APPROVED":
        tok = read_token()
        print(f"\ntoken present:  {tok is not None}"
              + (f"  (fp {token_fp(tok)})" if tok else " - run 'approve'"))
    print(f"\nledger:         {rel_to_root(LEDGER_FILE)} "
          f"({sum(1 for _ in LEDGER_FILE.open(encoding='utf-8')) if LEDGER_FILE.exists() else 0} events)")
    return 0


def cmd_reset(force: bool) -> int:
    if not force:
        sys.exit("REFUSED: reset discards the current gate. Pass --force to "
                 "reset to PENDING and delete the approval token.")
    clear_token()
    save_state(_blank_state())
    log_event(event="reset", actor="human", phase="PENDING")
    print("Gate reset to PENDING; approval token deleted.")
    return 0


# --------------------------------------------------------------------------- #
# local API (the trigger Routine B is fired through)
# --------------------------------------------------------------------------- #

class GateHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):          # keep the console quiet
        pass

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/status":
            state = load_state()
            payload = {k: state[k] for k in
                       ("phase", "run", "plan_path", "plan_sha256", "tag",
                        "target_commit", "approved_at", "fired_at")}
            self._json(200, {"ok": True, "state": payload})
        elif self.path in ("/", "/health"):
            self._json(200, {"ok": True, "name": "loop11 human gate"})
        else:
            self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/fire":
            self._json(404, {"ok": False, "error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception as exc:
            self._json(400, {"ok": False, "error": f"bad JSON body: {exc}"})
            return
        token = str(body.get("token") or "")
        claimed = str(body.get("plan_sha256") or "")
        code, result = do_fire(claimed, token, channel="http")
        self._json(code, result)


def cmd_serve(port: int) -> int:
    host = "127.0.0.1"
    try:
        server = http.server.ThreadingHTTPServer((host, port), GateHandler)
    except OSError as exc:
        sys.exit(f"cannot bind {host}:{port}: {exc}")
    print(f"Human-gate API listening on http://{host}:{port}")
    print("  GET  /status          current gate state")
    print("  POST /fire            fire Routine B  (body: token + plan_sha256)")
    print("Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Two-Routine Gate (loop11)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("draft", help="Routine A: author + seal a plan (no action)")
    sub.add_parser("seal", help="Routine A: seal an authored plan file").add_argument(
        "plan_file")
    sub.add_parser("approve", help="HUMAN: mint token, phase -> APPROVED")
    f = sub.add_parser("fire", help="Routine B: verify, then create the tag")
    f.add_argument("plan_sha256")
    f.add_argument("--token", required=True, help="the token printed by approve")
    s = sub.add_parser("serve", help="run the local API (curl target)")
    s.add_argument("--port", type=int, default=int(os.environ.get("GATE_PORT", 8787)))
    sub.add_parser("status", help="print gate state")
    r = sub.add_parser("reset", help="back to PENDING")
    r.add_argument("--force", action="store_true")

    args = ap.parse_args(argv)
    if args.cmd == "draft":
        return cmd_draft()
    if args.cmd == "seal":
        return cmd_seal(args.plan_file)
    if args.cmd == "approve":
        return cmd_approve()
    if args.cmd == "fire":
        return cmd_fire(args.plan_sha256, args.token)
    if args.cmd == "serve":
        return cmd_serve(args.port)
    if args.cmd == "status":
        return cmd_status()
    if args.cmd == "reset":
        return cmd_reset(args.force)
    ap.error(f"unknown command {args.cmd!r}")


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as exc:                      # surface errors readably
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
