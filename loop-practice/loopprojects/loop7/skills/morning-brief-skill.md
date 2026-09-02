# Morning-Brief Engine — Beat Contract (Loop 7)

You are the engine of the Loop 7 morning-brief loop, woken for **one beat**.
You have fresh context every beat: you do **not** remember previous runs. The
spine files are the memory. Work **only inside this folder**.

## What a beat does (in order)

0. **Check the hold.** Read the `State` value in `progress.md` → `## Last Run`.
   - If it is `NEEDS_HUMAN`: do **NOT** attempt the task. Append one
     `loop-log.md` row: `HOLD — escalated, waiting on human`. Reply
     `RUN <n> COMPLETE — HOLD` and stop.
1. **Read the spine.** Read `progress.md`, then `loop-log.md`.
2. **Deliver today's brief.** Read the file `source/daily-brief.txt`.
   - **SUCCESS path:** the file exists and is non-empty. Copy its text into
     `progress.md` under `## Findings` as a dated bullet, and record SUCCESS.
   - **FAILURE path:** the file is missing or empty. Do **NOT** create it, do
     **NOT** hunt for another filename, do **NOT** invent content. Record the
     failure only.
3. **Update the spine.** In `progress.md`, rewrite the `## Last Run` block:
   - `Run:` previous + 1.
   - `When:` today's date from your wake message (e.g. `2026-09-06`).
   - `Result:` `SUCCESS` or `FAILED`.
   - `Reason:` `—` on success; on failure the exact error, e.g.
     `source/daily-brief.txt not found`.
   - `Consecutive failures:` `0` on success; on failure = previous value + 1.
   - `State:` keep `RUNNING` (the escalation step below may change it).
4. **Append one row** to `loop-log.md`: Run #, date, **Attempt = the
   `Consecutive failures` count you just wrote** (a running number 1, 2, 3…),
   Result, short note.
5. **Escalation check** — only when you just recorded `Result: FAILED`. See
   the section below.
6. **Reply** with exactly one line:
   `RUN <n> COMPLETE — <SUCCESS|FAILED|ESCALATED|HOLD>`.

## Escalation (MAX_ATTEMPTS = 3) — added 2026-09-05 (observability fix)

_A loop that records a failure but never stops or pages anyone will burn a beat
every morning and never be noticed. This rule is that missing capability._

- **MAX_ATTEMPTS = 3.** When a run records `Result: FAILED` and the
  `Consecutive failures` count it just wrote is **3 or more**:
  1. Change `Result:` in `## Last Run` to **`ESCALATED`** and `State:` to
     **`NEEDS_HUMAN`** (leave `Reason` and `Consecutive failures` unchanged).
  2. Append a dated bullet under `## Needs Human` in `progress.md` that states
     **all** of:
     - **What failed:** `<Reason>` — the task could not be completed.
     - **Since when:** date of the first `FAILED` row of the current streak in
       `loop-log.md`.
     - **Attempts:** `<Consecutive failures> consecutive daily attempts`.
     - **Loop action:** stopped retrying — State set to `NEEDS_HUMAN`.
     - **First thing to check:** does `source/daily-brief.txt` exist?
  3. Append a `loop-log.md` row: `ESCALATED — Needs Human`.
  4. Reply `RUN <n> COMPLETE — ESCALATED`.
- While `State` is `NEEDS_HUMAN`, later beats **hold** (step 0) and burn no more
  attempts. A human resets `State` to `RUNNING` only after fixing the cause.

## Hard rules

- Never write outside this folder.
- Never modify `skills/`, `README.md`, `runs/`, or `cost.md`.
- Never fabricate the brief's content.
- On failure: record it, run the escalation check, then stop.
