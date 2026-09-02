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

---

## Results (project executed 2026-09-03; beats simulated as 09-04 → 09-07)

Each beat was a **real headless `claude -p` run** with no memory — usage was
measured, not guessed (`runs/*.json`, analysis in `cost.md`).

| Beat | When | Outcome | Measured in/out tokens |
|------|------|---------|------------------------|
| 1 | 2026-09-04 | FAILED — `source/daily-brief.txt not found` (recorded, no escalation) | 18,640 / 1,698 |
| 2 | 2026-09-05 | FAILED — same (still no escalation; spine audit exposes the gap) | 20,008 / 2,306 |
| 3 | 2026-09-06 | **ESCALATED** — `State: NEEDS_HUMAN`, structured Needs Human note | 25,713 / 7,971 |
| 4 | 2026-09-07 | **HOLD** — no new attempt, waits for the human | 19,750 / 1,439 |

**Diagnosis from the spine alone** (only `progress.md` + `loop-log.md`): the
brief was never delivered because the loop reads a file that does not exist
(`source/daily-brief.txt`), failing every morning from 2026-09-04; Runs 1–2
left **no** Needs Human note (the discovered gap), and after the escalation
rule was added, Run 3 wrote a clear note — what / since when / attempts /
stopped / first thing to check — and Beat 4 held. Full write-up in
`progress.md`.

**Cost:** ≈ 20k input + 2k output tokens per daily beat → ≈ 660k
tokens/month → roughly **$0.90–$4.50/month** at reference rates, dominated by
the ~18.5k-token per-invocation harness overhead (content is nearly free next
to it). A HOLD beat that does nothing still costs ~19.7k input tokens — so an
escalated loop should also stop its *scheduler*.

## Lessons (condensed; see progress.md)

1. **Legibility ≠ escalation.** Recording a failure each beat is necessary but
   not sufficient — without a policy that turns repeated failures into a
   "human needed" state and a throttle that then stops retrying, a loop fails
   silently forever.
2. **The spine told the truth because each beat was amnesiac.** Fresh-context
   runs with the files as the only memory is what made the diagnosis possible.
3. **Sabotage by misconfiguration is cheap to build and honest to run:** the
   loop pointed at a missing file never met its success condition, exactly as
   a real typo'd path would.

## Done-when (project checklist)

- [x] Loop scaffolded Project-3-style: `progress.md` (Last Run / Findings /
      Already Reported / Needs Human), `loop-log.md`, morning-brief engine.
- [x] Cost measured per run and projected monthly (`cost.md`).
- [x] Sabotaged (beat reads a file that never exists) with `MAX_ATTEMPTS = 3`.
- [x] Broken loop run; it failed for real (4 beats).
- [x] Failure diagnosable from the spine alone.
- [x] Loop left a clear Needs Human note instead of failing silently (the
      capability was missing, found by audit, and added).
