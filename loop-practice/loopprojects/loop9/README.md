# Loop 9 — Rehearse a Routine for Free

Goal: rehearse Claude Code's scheduled **Routine** feature end-to-end on a
throwaway task, *before* trusting it with anything real. The core lesson:
a routine run shows you a **status**, but only the **full transcript** tells you
what the run actually did.

Status of this rehearsal: **done** — one successful run + one deliberately
failed run, both captured as full transcripts under `routine/results/runs/`.

## The throwaway task

**Summarize the 5 most recent commits → publish a short markdown summary on
branch `claude/summary`.**

- Zero risk: touches only `loop9/routine/` + a throwaway `claude/summary`
  branch, never pushes.
- Deterministic: input hashes are pinned in `context.md`, so every run reads
  the same fixed input and can be compared fairly.

## Structure

```
loop9/routine/
  context.md          input the routine reads (5 pinned commit hashes)
  prompt.md           SELF-CONTAINED prompt — the GOOD run
  prompt-broken.md    identical, but Step 1 points at a nonexistent file — the FAIL run
  run-routine.sh      run either prompt once, unattended; capture status + full transcript
  render-transcript.js  turn a transcript.jsonl into readable text (every tool call)
  results/
    commit-summary.md   ← written by the GOOD run, committed onto claude/summary
    runs/
      01-good/        STATUS.json + transcript.jsonl + transcript.txt   (real success)
      02-broken/      STATUS.json + transcript.jsonl + transcript.txt   (real failure)
```

Both prompts are **self-contained**: a routine executes with zero conversation
history, so a prompt must carry everything — the goal, exact steps, the exact
file paths, hard constraints ("do not push"), and a definition of done. Both
prompts also tell the routine to **stop and report** if its required input is
missing. That rule is what turns the broken run into a visible failure instead
of a silent improvisation.

## How a Routine actually runs

A Routine is a **saved prompt run as a fresh, unattended session**. You see a
run list with a status; the interesting part is the session transcript behind
that status. Two facts matter:

1. The status is coarse. From the official docs: *"A green status in the run
   list means the session started and exited without an infrastructure error.
   It does not mean the task in your prompt succeeded."*
2. The transcript is ground truth: every tool call, error, and result — what
   the run *actually did*, not just whether the session survived.

## The two recorded runs

### Run 01 — GOOD (`routine/prompt.md`)
Status line: `subtype=success · is_error=false · terminal_reason=completed`
→ the run list would show **green**.

Transcript shows real work: read `context.md`, ran `git show` on all 5 hashes,
wrote `results/commit-summary.md`, created branch `claude/summary`, committed
exactly one file (`27e803b`), switched back to `main`, did not push.

Verify the artifact yourself:
```bash
git log claude/summary --oneline -1          # 27e803b routine: commit summary 2026-09-03
git show claude/summary:loop-practice/loopprojects/loop9/routine/results/commit-summary.md
```
Cost: ≈ $0.26.

### Run 02 — BROKEN (`routine/prompt-broken.md`, points at a file that doesn't exist)
Status line: `subtype=success · is_error=false · terminal_reason=completed`
→ the run list would STILL show **green**… yet the task failed.

The transcript shows the truth: the routine globbed, confirmed the input file
is absent, and stopped with **"Definition of done NOT met"** — no summary
written, no branch created, no commit made (`claude/summary` still at `27e803b`).

**This is the whole point.** The status column cannot distinguish run 01 from
run 02. Only opening the run and reading the transcript can. That is why you
must always inspect the transcript of any routine that matters — especially the
green ones.

Cost: ≈ $0.14.

## Exact next commands (re-run this yourself)

Everything below runs from the **git repo root**
(`C:/Users/The-laptop-store/Documents/GitHub/Loop-Engineering-Projects`).

Re-run the GOOD routine (one-off, unattended):
```bash
bash loop-practice/loopprojects/loop9/routine/run-routine.sh \
  loop-practice/loopprojects/loop9/routine/prompt.md 01-good
```

Re-run the BROKEN routine:
```bash
bash loop-practice/loopprojects/loop9/routine/run-routine.sh \
  loop-practice/loopprojects/loop9/routine/prompt-broken.md 02-broken
```

To read a run's full transcript as text (not just its status):
```bash
node loop-practice/loopprojects/loop9/routine/render-transcript.js \
  loop-practice/loopprojects/loop9/routine/results/runs/01-good/transcript.jsonl
```

`run-routine.sh` saves three artifacts per run:
- `STATUS.json` — the coarse status line (what the status column shows)
- `transcript.jsonl` — the FULL transcript, copied from the run's session file
- `transcript.txt` — that transcript rendered readably (run render-transcript.js)

## Notes on the real `/schedule` (cloud) feature

This rehearsal is a faithful local stand-in. Claude Code also has a native
cloud Routine feature: run `/schedule` in any session (alias `/routines`) or
manage routines at `claude.ai/code/routines`; each routine runs as a full cloud
session on a clone of your repo; `Run now` (web) or `/schedule run` (CLI) starts
a one-off; each run gets a status + an "open the run" transcript.

Why this environment used the local stand-in instead: `/schedule` requires a
**claude.ai subscription (OAuth) login**. This machine authenticates to an
API-key/gateway setup (`ANTHROPIC_API_KEY` is set, model routes via a gateway),
which makes the CLI hide `/schedule` — so the cloud feature is not reachable
here. If you later log in with a claude.ai account (Pro/Max/Team/Enterprise),
the same two prompt files drop straight into a routine: set the repo to
`Amnagithub/Loop-Engineering-Projects`, run it once via **Run now**, then click
the run to read its full transcript. Cloud routines auto-create
`claude/`-prefixed branches, so `claude/summary` is exactly the branch shape
they allow.
