#!/usr/bin/env python3
"""Secrets Drill (Project 10) - deterministic harness.

Runs the same one-secret task (drill/task.py) in three environments to show
WHY a gitignored .env secret fails on a cloud Routine and WHY an environment
variable succeeds:

  1. local     your real checkout (drill/.env is present)
               -> secret loaded from the .env file            -> SUCCESS
  2. cloud     a simulated cloud clone: ONLY git-tracked files are copied,
               so the gitignored drill/.env is absent
               -> the .env route finds nothing                -> FAIL
  3. panel     the same cloud clone, but the secret is injected as an
               environment variable (exactly what a Routine env-var panel or a
               GitHub Actions secret mapped into a step env does)
               -> secret read from the environment             -> SUCCESS

The clone simulation is mechanical: the drill copies precisely the files
`git ls-files` reports - the files git would send to a fresh clone. A
gitignored file is not among them, which is the whole point.

Usage:
    python run-drill.py            run all three arms (exit 0 if the drill
                                   shows the expected pattern)
    python run-drill.py local      run the local (.env) arm only (exit 0)
    python run-drill.py cloud      run the cloud .env arm only - the FAILING
                                   version (exit 1, the failure IS the result)
    python run-drill.py panel      run the cloud env-var arm only (exit 0)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SECRET = "DUMMY_SECRET_TOKEN"

HERE = Path(__file__).resolve().parent           # .../loop10/drill
LOOP10 = HERE.parent                              # .../loop10
SCRATCH = LOOP10 / ".drill-clone"
CLONE = SCRATCH / "work"                          # simulated cloud checkout
RESULTS = SCRATCH / "results"


def repo_root() -> Path:
    out = subprocess.run(
        ["git", "-C", str(HERE), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    )
    return Path(out.stdout.strip())


def read_dotenv(path: Path) -> dict[str, str]:
    """Tiny .env parser (stdlib only)."""
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def build_clone() -> Path:
    """Copy exactly the git-tracked drill files into CLONE."""
    root = repo_root()
    drill_rel = HERE.relative_to(root).as_posix()
    tracked = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--", drill_rel],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    if not tracked:
        sys.exit(
            "ERROR: nothing tracked under loop10/drill yet.\n"
            "  A cloud clone contains ONLY committed files. Commit the loop10 "
            "files first (git add loop10 && git commit), then re-run this drill."
        )
    if CLONE.exists():
        shutil.rmtree(CLONE)
    for rel in tracked:
        src = root / rel
        dst = CLONE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return CLONE / drill_rel


def clean_env(secret: str | None = None) -> dict[str, str]:
    """Child environment: never leak a stray DUMMY_* var from the parent, so
    each arm tests exactly its own channel."""
    env = dict(os.environ)
    for key in list(env):
        if key == SECRET or key.startswith("DUMMY"):
            env.pop(key, None)
    if secret:
        env[SECRET] = secret
    return env


def run_task(cwd: Path, proof: Path, secret: str | None) -> int:
    proof.parent.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(cwd / "task.py"), "-o", str(proof)]
    proc = subprocess.run(cmd, cwd=str(cwd), env=clean_env(secret),
                          capture_output=True, text=True)
    if proc.returncode == 0:
        print(f"        task.py: {proc.stdout.strip()}")
    else:
        print(f"        task.py (exit {proc.returncode}):")
        for line in (proc.stderr.strip() or proc.stdout.strip()).splitlines():
            print(f"          {line}")
    return proc.returncode


def check_ignore_rule() -> str | None:
    root = repo_root()
    rel = HERE.joinpath(".env").relative_to(root).as_posix()
    proc = subprocess.run(["git", "-C", str(root), "check-ignore", "-v", rel],
                          capture_output=True, text=True)
    return proc.stdout.strip() or None


def banner() -> None:
    print("=" * 74)
    print("SECRETS DRILL  (Project 10)   one secret, three environments")
    print("=" * 74)
    print(f"  secret            {SECRET}")
    print(f"  git root          {repo_root()}")
    rule = check_ignore_rule()
    if rule:
        print(f"  .env ignore rule  {rule}")
    else:
        print("  WARNING           drill/.env is NOT gitignored - add '.env' to "
              "loop10/.gitignore before continuing")
    print(f"  cloud clone sim   {CLONE}  (only git-tracked files)")


def arm_local(value: str) -> tuple[str, list[str]]:
    print("\nARM 1 - local checkout   (channel: read .env -> export -> task)")
    lines = ["drill/.env exists here, so the .env route finds the secret.",
             "This is the trap: it works on your machine..."]
    rc = run_task(HERE, RESULTS / "arm1-local/proof.json", value)
    ok = rc == 0
    lines.append("SUCCESS on the local checkout." if ok else "FAILED even locally.")
    return ("SUCCESS" if ok else "FAIL"), lines


def arm_cloud_dotenv(clone_drill: Path) -> tuple[str, list[str]]:
    print("\nARM 2 - cloud clone      (channel: read .env -> export -> task)")
    print("        EXPECTED FAIL: the .env version must break in a clone")
    env_file = clone_drill / ".env"
    if env_file.exists():
        return "FAIL(committed)", [
            f"{env_file} IS present in the clone.",
            "That means .env was committed despite .gitignore - remove it from "
            "git. The drill requires it to be absent."]
    return "FAIL", [
        f"{env_file} is NOT in the clone.",
        "git clones only committed files; .env is gitignored, so a fresh clone "
        "never contains it.",
        f"The .env route has nothing to load -> {SECRET} never reaches the task.",
        "This is exactly what a cloud Routine hits when a prompt reads .env.",
    ]


def arm_panel(clone_drill: Path, value: str) -> tuple[str, list[str]]:
    print("\nARM 3 - cloud clone + env var   (channel: platform env)   EXPECTED OK")
    lines = ["No .env file is touched. The secret is injected into the run's",
             "environment (as a Routine env-var panel / GitHub Actions secret "
             "would).",
             f"Value used here = {value} (read from the local drill/.env so it "
             "is not duplicated; in production you type it in the secret store, "
             "not in a file)."]
    rc = run_task(clone_drill, RESULTS / "arm3-panel/proof.json", value)
    ok = rc == 0
    return ("SUCCESS" if ok else "FAIL"), lines


def secrets_match() -> bool:
    """Arm 1 and arm 3 succeeded via different channels - confirm they used the
    SAME secret (same HMAC over the same probe)."""
    try:
        a = json.loads((RESULTS / "arm1-local/proof.json").read_text(encoding="utf-8"))
        b = json.loads((RESULTS / "arm3-panel/proof.json").read_text(encoding="utf-8"))
        return a["probe_hmac_sha256"] == b["probe_hmac_sha256"]
    except Exception:
        return False


def summary(outcomes: dict[str, str]) -> int:
    expected = {"1-local": "SUCCESS", "2-cloud": "FAIL", "3-panel": "SUCCESS"}
    print("\n" + "-" * 74)
    ok = True
    for arm in ("1-local", "2-cloud", "3-panel"):
        good = outcomes[arm] == expected[arm]
        ok = ok and good
        print(f"  {'[ ok ]' if good else '[ ?? ]'}  {arm:<8} "
              f"expected {expected[arm]:<8} got {outcomes[arm]}")
    same = secrets_match()
    ok = ok and same
    print(f"  {'[ ok ]' if same else '[ ?? ]'}  arm1 and arm3 signed with the "
          f"same secret: {same}")
    print("-" * 74)
    if ok:
        print("DRILL PASS: a gitignored .env secret is unreachable in a cloud clone;")
        print("an environment variable delivered by the platform is the right channel.")
    else:
        print("DRILL DID NOT PASS - read the arm output above.")
    return 0 if ok else 2


def main(argv: list[str]) -> int:
    mode = argv[1] if len(argv) > 1 else "all"
    if mode not in ("all", "local", "cloud", "panel"):
        sys.exit(f"usage: python run-drill.py [all|local|cloud|panel]")

    dotenv_file = HERE / ".env"
    if not dotenv_file.exists():
        sys.exit(
            f"ERROR: {dotenv_file} is missing.\n"
            "  Copy drill/.env.example to drill/.env and set "
            f"{SECRET}=DUMMY_SECRET_TOKEN_12345, then re-run."
        )
    value = read_dotenv(dotenv_file).get(SECRET, "")
    if not value:
        sys.exit(f"ERROR: {SECRET} is empty in {dotenv_file}.")

    banner()

    outcomes: dict[str, str] = {}
    if mode in ("all", "local"):
        outcome, lines = arm_local(value)
        for line in lines:
            print(f"        {line}")
        outcomes["1-local"] = outcome

    clone_drill: Path | None = None
    if mode in ("all", "cloud", "panel"):
        clone_drill = build_clone()
        n_files = sum(1 for p in CLONE.rglob("*") if p.is_file())
        print(f"        clone built from {n_files} tracked file(s); "
              f".env present in clone: {(clone_drill / '.env').exists()}")

    if mode in ("all", "cloud"):
        outcome, lines = arm_cloud_dotenv(clone_drill)  # type: ignore[arg-type]
        for line in lines:
            print(f"        {line}")
        outcomes["2-cloud"] = outcome
        if mode == "cloud":
            print("\n  The .env version FAILS in a cloud clone (that is the "
                  "lesson).")
            print("  Exit code 1 mirrors the failure so scripts see it as a "
                  "failure.")
            return 0 if outcome != "SUCCESS" else 1

    if mode in ("all", "panel"):
        outcome, lines = arm_panel(clone_drill, value)  # type: ignore[arg-type]
        for line in lines:
            print(f"        {line}")
        outcomes["3-panel"] = outcome
        if mode == "panel":
            return 0 if outcome == "SUCCESS" else 1

    return summary(outcomes)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
