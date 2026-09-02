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

## Diagnosis — from the spine alone (read only progress.md + loop-log.md)

_Project 7 Part 5, answered as a fresh human would: no engine conversation, no
re-reading of the runs — only the two spine files above._

1. **What failed?** The morning brief was never delivered. Every beat failed
   its one task step identically: `source/daily-brief.txt not found`. The loop
   was pointed at a file that does not exist, so its success condition could
   never be met.
2. **When did it fail?** Runs 1 and 2 failed on 2026-09-04 and 2026-09-05
   while the contract had no escalation; Run 3 failed again on 2026-09-06 and
   escalated. The root cause was present from the very first beat.
3. **Did the loop leave a clear "Needs Human" note?** After Runs 1–2: **no** —
   `## Needs Human` read `_none yet_` and `State` stayed `RUNNING`. A loop with
   that contract fails silently every morning forever; a reader can *infer*
   trouble from two identical FAILED rows, but the loop never declares it needs
   a human. After the escalation capability was added (2026-09-05) and Run 3
   fired, the note is unambiguous (see `## Needs Human`): what failed, since
   when, how many attempts, that it stopped, and the first thing to check. Beat
   4 then **HOLD**ed (loop-log, 2026-09-07) instead of burning another attempt.

## The gap found and fixed (the second sabotage)

The planted failure was the missing file. The *discovered* gap was subtler and
more important: the initial contract knew how to **record** a failure but had
no rule to **escalate** one. Failing silently is not only about writing an
error row — it is the loop never telling anyone it is stuck and never stopping.
Fixed by adding `MAX_ATTEMPTS = 3`, `State: NEEDS_HUMAN`, and the HOLD rule to
`skills/morning-brief-skill.md` (commit e749edd).

## Lessons learned

- **A loop needs three observability layers, not one:** (1) *legibility* —
  every beat writes its result to the spine (this loop had it); (2) *policy* —
  a rule that turns N failures into "a human is needed" (this was the missing
  part); (3) *throttle* — stop retrying once escalated (added via HOLD).
  Without (2) and (3), layer (1) produces a log nobody reads.
- **The Needs Human entry must carry recovery context**: what, since when, how
  many attempts, loop action, first thing to check. A bare date + error string
  does not tell a human what to do next.
- **Deterministic failures could escalate immediately**, but a cap still matters
  for transient failures; MAX_ATTEMPTS = 3 handled both in this design.
- **Fresh-context beats are what make the spine trustworthy**: every engine ran
  with no memory of previous beats — the files genuinely carried the story.

## Cost of this loop (summary — full derivation in `cost.md`)

Measured per beat ≈ **20k input + 2k output tokens** (beats 1–4, real runs).
At once-per-day that is ≈ **660k tokens/month**, roughly **$0.90–$4.50/month**
at Haiku→Opus reference rates — dominated by the ~18.5k-token harness overhead
paid on *every* run regardless of task. The actual bill depends on this
machine's configured backend rate. Extra finding: an escalated loop that stays
scheduled still burns the full daily overhead doing nothing — stop the timer,
not just the beat.

## Recovery (next step for the human)

To resume: (1) drop the brief at `source/daily-brief.txt`, (2) set `State:
RUNNING` and `Consecutive failures: 0` in `## Last Run`, (3) wake the next
beat — it should go `SUCCESS`. Not run here; this project's done-condition is
the escalation note above, which is now in place.
