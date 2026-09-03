# Observed runs — the fleet log the Dreaming Loop dreams over

This file is loop12's INPUT corpus: dated run rows that the fleet of loop
drills recorded. It stands in for "the loops' own recent logs"; in a real
deployment `scan.py` would point at the live loops' logs instead, and this
fixture would not exist.

> **Drill note (read this):** rows `5` and `6` below are the **deliberately
> planted repeated failure** for Project 12's demo beat. Both record the same
> stall on 2026-09-03 so the deterministic scanner must catch a signature that
> appears twice and turn it into a proposal. See `README.md` / `loop-log.md`.
> Everything else is plain SUCCESS context.

| Run | Project | Date | Result | Notes |
|-----|---------|------|--------|-------|
| 1 | loop3 debt-scan | 2026-09-03 | SUCCESS | workspace clean, no findings |
| 2 | loop8 daily-scan | 2026-09-03 | SUCCESS | checker PASS, 0 open markers |
| 3 | loop10 secrets | 2026-09-03 | SUCCESS | all three drill arms passed |
| 4 | loop11 gate | 2026-09-03 | SUCCESS | approve + fire ok, tag created |
| 5 | loop12e staging | 2026-09-03 | FAILED | beat stalled: headless claude -p child ran in an untrusted temp dir and blocked on the folder-trust prompt |
| 6 | loop12e staging | 2026-09-03 | FAILED | beat stalled: headless claude -p child ran in an untrusted temp dir and blocked on the folder-trust prompt |
