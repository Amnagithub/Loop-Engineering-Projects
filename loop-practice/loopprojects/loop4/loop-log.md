# Loop Log

## Iteration 1 (2026-09-01)

- **Implementer:** created branch `fix/project4-bugs`, committed baseline
  (`b86a78b`), fixed both bugs in `buggy.py` (`2212c32`).
- **Tests:** `python3 test_buggy.py` → "All tests passed!" (2/2).
- **Reviewer:** strict review of `2212c32` vs `skills/fix-skill.md` → **PASS**.
- **PR:** NOT opened — no git remote configured, `gh` CLI not installed,
  `git push` fails ("No configured push destination").

## Iteration 2 (2026-09-02) — GitHub-connected re-run

- **Setup:** `buggy.py` on `main` had been snapshotted in its already-fixed
  form; restored the two intentional bugs on `main` (`3d8c69d`) so tests fail
  and the fix flow has a real change to deliver.
- **Implementer:** created branch `fix/project4-bugs` off buggy `main`, fixed
  both bugs (`ee0a230`).
- **Tests:** `test_buggy.py` → "All tests passed!" (2/2).
- **Reviewer:** re-read `loopprojects/skills/fix-skill.md` + full diff → **PASS**
  (diff limited to the two buggy lines, `test_buggy.py` untouched, both expected
  values hold).
- **Push/PR:** pending — needs GitHub authentication (no `gh` CLI, no stored
  credentials).
