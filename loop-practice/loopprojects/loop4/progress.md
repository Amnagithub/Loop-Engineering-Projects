# Progress

## Start (2026-09-01)

- Created `buggy.py` with two intentional bugs: `calculate_total` (wrong
  calculation) and `countdown` (off-by-one).
- Created `test_buggy.py` with two tests that currently fail.
- Created `skills/fix-skill.md` describing the fix and PASS/FAIL criteria.
- Next step: run the maker-checker flow (Implementer → Reviewer) and fix the
  bugs until the review is PASS, then open a PR.

## Fix Loop (2026-09-01)

- Implementer created branch `fix/project4-bugs` (baseline commit `b86a78b`).
- Fixed both bugs in `buggy.py` (commit `2212c32`):
  - `calculate_total` → `price * quantity`
  - `countdown` → `range(n, -1, -1)` (includes 0)
- Tests: `python3 test_buggy.py` → all 2 tests pass.
- Reviewer verdict: **PASS** (matches all criteria in `skills/fix-skill.md`).
- PR step: **blocked** — no git remote configured and `gh` CLI not installed,
  so `git push` fails and no PR can be opened from this environment.

## GitHub-Connected Re-run (2026-09-02)

- `main` had been snapshotted in the already-fixed form, so the canonical
  Project-4 start state was restored on `main` (commit `3d8c69d`): both
  intentional bugs are back and `test_buggy.py` fails as the README expects.
- Implementer created branch `fix/project4-bugs` off the buggy `main` and fixed
  both bugs (commit `ee0a230`):
  - `calculate_total` → `price * quantity`
  - `countdown` → `range(n, -1, -1)` (includes 0)
- Tests: `test_buggy.py` → "All tests passed!" (2/2). Test file untouched.
- Reviewer verdict: **PASS** — the diff matches every criterion in
  `loopprojects/skills/fix-skill.md`.
- Pushed `main` (`4a8e505`, buggy baseline + docs) and `fix/project4-bugs`
  (`ee0a230`) to `origin`.
- **PR opened:** [Amnagithub/Loop-Engineering-Projects#1](https://github.com/Amnagithub/Loop-Engineering-Projects/pull/1)
  — base `main`, head `fix/project4-bugs`; diff is exactly `buggy.py`
  (mergeable, 1 file changed). Created after the Reviewer PASS.
