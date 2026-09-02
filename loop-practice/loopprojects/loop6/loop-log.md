# Loop log — Project 6 (Doorbell, event-driven)

| Beat | When | Ring source | What happened | Verdict |
|---|---|---|---|---|
| scaffold | 2026-09-03 | human prompt | buggy.py + test_buggy.py + review-skill.md created; bug confirmed locally (`AssertionError`) | — |
| wire | 2026-09-03 | human prompt | `.github/workflows/doorbell-review.yml` added at repo root; pushed to `main` | — |
| split | 2026-09-03 | human prompt | `main` corrected (suite green); planted bug parked on `doorbell/planted-bug` | PASS (on `main`) |
| first ring | 2026-09-03 | **PR #2 opened** (`doorbell/planted-bug` → `main`) | automatic review posted itself, **no prompt typed**: `**Verdict: FAIL**` quoting `AssertionError` (only 2 of 3 events delivered); run concluded `failure` (red check) | **FAIL (bug flagged) ✓** |
| (next) | | add `ANTHROPIC_API_KEY` secret | re-ring to get the Claude Code prose review (file:line finding) | — |
| (next) | | fix PR / `synchronize` | push the correct fix; expect automatic **PASS** | — |
