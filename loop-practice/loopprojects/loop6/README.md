# Project 6 — The Doorbell Loop (event-driven)

The loop no longer needs you to prompt it. A **doorbell** waits outside: the
moment a Pull Request rings in, the review runs **by itself** — no human types
a prompt, the bell is the heartbeat.

## The idea

A one-shot pipeline needs a **heartbeat** to become a real loop (the missing
piece flagged at the end of Project 5). In this project the heartbeat is a
*GitHub event*: `pull_request` opened. Each PR is a doorbell press; the ring
wakes an automated reviewer, which checks the arriving code against a written
contract and posts its verdict back onto the PR.

So the review body is now **event-driven**:

> **PR opens (the ring) → reviewer wakes (no prompt) → reads the contract →
> runs the tests → posts PASS/FAIL findings on the PR.**

## The files in this project

- `buggy.py` — the Doorbell module: an event dispatcher (`handle_all`) with one
  planted **off-by-one** bug. The last queued doorbell press is never delivered.
- `test_buggy.py` — the spec as tests; fails against `buggy.py`.
- `skills/review-skill.md` — the reviewer contract: what the code must do, the
  class of bug to hunt (off-by-one that drops the last event), how to verify,
  and how to report (`VERDICT: FAIL/PASS`).
- `README.md` — this file.
- `progress.md` — the spine: where this project is and what is next.
- `loop-log.md` — per-beat log of the Doorbell firing.

## The doorbell wiring (what makes it ring by itself)

At the **repository root** (this folder lives inside the
`Loop-Engineering-Projects` repo):

- `.github/workflows/doorbell-review.yml` — a GitHub Action that fires on
  `pull_request` (opened / reopened / synchronized) for paths under
  `loop-practice/loopprojects/loop6/`, checks out the PR, runs the tests, and
  runs a headless Claude Code reviewer against the diff. Requires one secret:
  `ANTHROPIC_API_KEY`, set in the repo's GitHub settings.

GitHub Actions only reads workflow files from `.github/workflows/` at the repo
**root**, not per-project folders — which is why the wiring lives one level up
from this project directory.

## Try it (the demo ring)

1. Add the `ANTHROPIC_API_KEY` secret to the repo on GitHub.
2. Push the branch `doorbell/planted-bug` and open a PR from it against `main`.
   That branch carries a buggy `buggy.py` (the planted bug).
3. The Action fires automatically. Watch the PR: a review appears — no prompt
   typed — flagging the off-by-one and the failing test.

## Environment note

`python`/`python3` on the local PATH are broken WindowsApps stubs; locally use
`C:\Python314\python.exe`. On the GitHub runner, `python3` is fine.

## Pipeline → loop, where this sits

| Piece | Project |
|---|---|
| One-shot body (draft → reviewer PASS/FAIL → merge) | 5 |
| **Heartbeat** (event wakes the body, no prompt) | **6 — this project** |
| Spine / progress memory (resume across beats) | `progress.md` + memory index |

The doorbell is one heartbeat source. The same body could be rung by a timer
(cron), a comment mention, or a file change — the event is the only thing that
changes.
