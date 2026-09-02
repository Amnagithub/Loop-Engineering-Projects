# Project 5 — Codify the Body (combined setup + run)

Turn the Project 4 style flow (**Implementer → Reviewer (PASS/FAIL) → merge on
PASS**) into one reusable unit that runs end-to-end in a single go.

## The codified body

One iteration of the body is:

**draft a candidate fix → run a strict independent reviewer that replies only
PASS or FAIL → collect the verdict.**

This project ships that body as files plus branches:

- `buggy.py` — two intentional bugs (the problem to fix).
- `test_buggy.py` — two tests that fail against `buggy.py`.
- `skills/fix-skill.md` — the contract: what a fix may and may not do, with
  explicit PASS/FAIL criteria.
- Candidate branches (`fix/loop5-*`) — 2–3 candidate fixes, each implemented
  and independently reviewed.
- `progress.md` — notes on progress.
- `loop-log.md` — log of each iteration.

## Flow (one go, no step-by-step prompting)

1. Set up the buggy problem + skill contract on `main` (baseline; tests fail).
2. For each candidate branch: implement a fix, run the tests, and have an
   independent reviewer answer only **PASS** or **FAIL**.
3. Collect the verdicts; a candidate merges **only** on PASS.

## Environment note

`python`/`python3` on PATH are WindowsApps stubs that error out. The canonical
interpreter used for this project is `C:\Python314\python.exe`.

## Pipeline, not a loop

The whole run executes once and then stops. See `progress.md` for why this is a
single-pass pipeline and for the two pieces (heartbeat + spine/progress memory)
that would turn it into a real loop.
