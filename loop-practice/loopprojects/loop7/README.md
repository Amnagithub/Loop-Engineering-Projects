# Project 7 — Break It On Purpose (Observability + Cost)

A daily **morning-brief loop**, then deliberately sabotaged so it fails, so we can
learn whether the loop *tells us* it needs a human — and what one daily run costs.

## The loop

> **morning timer → a fresh engine wakes (no memory) → reads `progress.md` (the
> spine) + `loop-log.md` → reads the day's brief at `source/daily-brief.txt` →
> updates the spine + log → stops.**

Each beat is a **headless Claude Code invocation** (`claude -p`, one run, no
memory) — the same deployment shape Project 6 used for its reviewer. Because a
beat is a real CLI process, per-run token usage is **measured, not guessed**
(see `runs/` and `cost.md`).

## Files

- `progress.md` — the spine. Sections: **Last Run / Findings / Already
  Reported / Needs Human** (+ final diagnosis and lessons at the bottom).
- `loop-log.md` — one row per beat (the heartbeat's paper trail).
- `skills/morning-brief-skill.md` — the engine contract every beat follows.
- `source/` — where a producer is *supposed* to drop `daily-brief.txt` each
  morning. **It never does.**
- `runs/` — raw JSON of each beat run (usage tokens, result, session id).
- `cost.md` — measured tokens per run and the monthly cost projection.

## The sabotage (what was broken on purpose)

The beat's success condition is *"read and deliver `source/daily-brief.txt`"*.
That file **does not exist** and never will — the beat is pointed at a file that
is not there, so the success condition can never be met. The contract caps this
with **MAX_ATTEMPTS = 3** before the loop must stop and say so.

A second, subtler gap is hunted on purpose too: a loop that records a failure
but has **no rule that escalates it to a human** will burn a beat every morning
and never tell anyone. Whether the spine alone reveals that is the project's
question. _(Results and lessons are appended below once the run is done.)_
