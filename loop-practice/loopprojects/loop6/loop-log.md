# Loop log — Project 6 (Doorbell, event-driven)

| Beat | When | Ring source | What happened | Verdict |
|---|---|---|---|---|
| scaffold | 2026-09-03 | human prompt | buggy.py + test_buggy.py + review-skill.md created; bug confirmed (AssertionError, exit 1) | — |
| wire | 2026-09-03 | human prompt | `.github/workflows/doorbell-review.yml` added at repo root; pushed to main (`b006014`) | — |
| split | 2026-09-03 | human prompt | `main` corrected (suite green); planted-bug version parked on `doorbell/planted-bug` | PASS (on main) |
| (next) | | `pull_request` opened | first automatic ring — open `doorbell/planted-bug` → `main`, no prompt typed | FAIL expected (flag off-by-one) |
