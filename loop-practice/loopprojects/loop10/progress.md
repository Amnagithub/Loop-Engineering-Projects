# Progress

## Start (2026-09-03)

- Goal (Project 10 – The Secrets Drill): learn why a `.env`-based secret fails
  in a cloud/Routine environment and how to provide secrets correctly.
- Created the drill:
  - `drill/.env` holds the DUMMY token `DUMMY_SECRET_TOKEN_12345` (gitignored).
  - `drill/task.py` — one-secret task that reads `DUMMY_SECRET_TOKEN` from the
    process environment only and HMAC-signs a fixed probe into `proof.json`.
  - `drill/run-drill.py` — deterministic 3-arm harness: local checkout (`.env`
    present → SUCCESS, the trap), simulated cloud clone (only `git ls-files`
    content → `.env` absent → FAIL), cloud clone + env var injected (→ SUCCESS).
  - `drill/prompt-env-file.md` — WRONG routine prompt (reads `.env`).
  - `drill/prompt-env-var.md` — RIGHT routine prompt, carries the mandated line:
    "Credentials are available as environment variables; do not look for a .env file."
  - `README.md`, `.gitignore`, `.env.example`.
- Mechanical core: the cloud clone simulation copies precisely the files
  `git ls-files` reports; a gitignored `.env` is not among them — the same
  reason a real Routine's fresh clone never has it.
- Next: verify the harness (all three arms), commit the drill files (NOT `.env`).

## Done ✅ (2026-09-03)

- Verified with the real interpreter (`C:/Python314/python.exe`):
  - `git check-ignore -v drill/.env` shows the ignore rule.
  - Full drill (`run-drill.py`) → arm 1 SUCCESS, arm 2 FAIL (`.env` absent in
    the clone), arm 3 SUCCESS → `DRILL PASS`; arm 1 and arm 3 signed with the
    same secret (identical HMAC).
  - `run-drill.py cloud` → the failing `.env` version, exit 1 as intended.
  - `run-drill.py panel` → the env-var version, exit 0.
- Lesson recorded: a gitignored file never reaches the cloud clone, so secrets
  must be delivered as environment variables (Routine env-var panel / GitHub
  Actions secret → step env), and the prompt must say credentials are in env
  vars, not in a `.env` file.
