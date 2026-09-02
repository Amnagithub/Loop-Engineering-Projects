# Progress — Project 7 (Break It On Purpose: Observability + Cost)

The morning-brief loop: every morning a fresh engine reads this spine, delivers
today's brief from `source/daily-brief.txt` into Findings, and updates this
file + `loop-log.md`. The engine has no memory between beats — this file *is*
its memory.

## Last Run

- **Run:** 3
- **When:** 2026-09-06
- **Result:** ESCALATED
- **Reason:** `source/daily-brief.txt not found`
- **Consecutive failures:** 3
- **State:** NEEDS_HUMAN _(RUNNING | NEEDS_HUMAN)_

## Findings

_(The engine copies the day's brief here on SUCCESS. Nothing has run yet.)_

## Already Reported

_(Things surfaced to a human in earlier beats so they aren't repeated.)_

- _none yet_

## Needs Human

_(Anything a person must decide or act on. This section must stay empty only
while nothing needs a human.)_

- **2026-09-06** — **What failed:** `source/daily-brief.txt not found` — the task could not be completed.
  **Since when:** 2026-09-04. **Attempts:** 3 consecutive daily attempts.
  **Loop action:** stopped retrying — State set to `NEEDS_HUMAN`.
  **First thing to check:** does `source/daily-brief.txt` exist?
