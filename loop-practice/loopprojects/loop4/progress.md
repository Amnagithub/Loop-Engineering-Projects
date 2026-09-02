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
