# Progress — Project 6 (Doorbell, event-driven)

## Start (2026-09-03)

- **Goal:** the reviewer must run on its own — a GitHub PR event (the doorbell)
  wakes it; no human prompt; it must flag the planted bug.
- Created the buggy module + contract:
  - `buggy.py` — `handle_all(events, handler)` with a planted **off-by-one**:
    it iterates `events[:-1]`, so the **last** event is never delivered and the
    returned count is one short (a doorbell ring that goes unanswered).
  - `test_buggy.py` — `test_handle_all_delivers_every_event` (3 events → all 3
    delivered, count 3) fails against the bug; `test_handle_all_with_no_events`
    passes. Verified locally with `C:\Python314\python.exe`: AssertionError,
    exit 1.
  - `skills/review-skill.md` — the reviewer contract (dispatch spec, the class
    of bug to hunt, verify-by-running-tests, `VERDICT: FAIL/PASS` reporting,
    read-only).
- **Environment notes:** `python`/`python3` on PATH are broken WindowsApps
  stubs; local interpreter is `C:\Python314\python.exe`. `gh` CLI is **not**
  installed on this machine. Origin is a single GitHub repo
  (`Amnagithub/Loop-Engineering-Projects`) holding loop1–6, so the GitHub
  Action wiring must live at the repo root under `.github/workflows/`.

## Doorbell wiring (event trigger)

- `.github/workflows/doorbell-review.yml` added at the repo root: fires on
  `pull_request` for `loop6/**`, checks out the PR, runs the tests, then runs a
  headless reviewer against the diff + contract and posts findings on the PR.
- Requires one repo secret on GitHub: `ANTHROPIC_API_KEY`.

## Not yet done

- [ ] Demo ring: push `doorbell/planted-bug`, open the PR, watch the auto
  review flag the bug.
- [ ] (Optional) A fix PR and a review that returns PASS, proving the gate
  has teeth in both directions.
- [ ] (Later) Broaden the paths filter so the doorbell rings for any loop.

## Lesson being built toward

The heartbeat existed as a concept in Project 5; this project gives it a real
source (a GitHub event) and a real actor (a headless reviewer). The remaining
step to a durable loop is resumable state across beats — the spine — carried by
this `progress.md` and the shared memory index.
