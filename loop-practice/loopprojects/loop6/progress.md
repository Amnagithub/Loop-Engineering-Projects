# Progress — Project 6 (Doorbell, event-driven)

## Start (2026-09-03)

- **Goal:** the reviewer must run on its own — a GitHub PR event (the doorbell)
  wakes it; no human prompt; it must flag the planted bug.
- Built the buggy module + contract (scaffold commit `b006014`):
  - `buggy.py` — `handle_all(events, handler)` with a planted **off-by-one**:
    it iterates `events[:-1]`, so the **last** event is never delivered and the
    returned count is one short (a doorbell ring that goes unanswered).
  - `test_buggy.py` — `test_handle_all_delivers_every_event` (3 events → all 3
    delivered, count 3) fails against the bug; `test_handle_all_with_no_events`
    passes. Verified with `C:\Python314\python.exe` (AssertionError → then green
    after the fix).
  - `skills/review-skill.md` — the reviewer contract: dispatch spec, the bug
    class to hunt (off-by-one that drops the last queued event),
    verify-by-running-tests, `VERDICT: FAIL/PASS` reporting, read-only.
- **Environment notes:** `python`/`python3` on PATH are broken WindowsApps
  stubs; local interpreter `C:\Python314\python.exe`. `gh` CLI **not** installed
  on this machine. Origin is one GitHub repo (`Amnagithub/Loop-Engineering-Projects`)
  holding loop1–6, so the GitHub Action must live at the repo root
  (`.github/workflows/doorbell-review.yml`).

## Doorbell wiring (event trigger, pushed to `main`)

- `.github/workflows/doorbell-review.yml` at the repo root: fires on
  `pull_request` (opened / reopened / synchronize) for `loop6/**`, checks out the
  PR, runs the suite (Ring 1), optionally runs a headless Claude Code review
  (Ring 2, gated on the `ANTHROPIC_API_KEY` secret), posts one automatic review
  comment (Ring 3), and leaves a red check when the verdict is FAIL (Ring 4).
- Requires: GitHub Actions enabled + one repo secret `ANTHROPIC_API_KEY` for the
  Claude review. The deterministic test review works without the secret.

## Demo arrangement (2026-09-03)

To make "open a PR that contains the planted bug" literal, the bug was split off
`main`:

- `main` now holds the **corrected** dispatcher (tests 2/2 pass).
- `doorbell/planted-bug` holds the **planted-bug** version (scaffold state), so
  a PR from it into `main` shows the bug in its diff.

## Not yet done

- [ ] Add the `ANTHROPIC_API_KEY` secret on GitHub (Settings → Secrets and
      variables → Actions) so the Claude skill-review ring fires.
- [ ] Demo ring: open the PR `doorbell/planted-bug` → `main`; the doorbell
      should post an automatic **FAIL** review flagging the off-by-one and the
      failing test — with no prompt typed.
- [ ] Close that PR unmerged (`main` is already correct) or, to see a merge
      cycle, first break `main` again on a fresh branch.
- [ ] (Later) Widen the paths filter so the doorbell rings for every loop.

## Lesson being built toward

Project 5's missing piece was the **heartbeat**. Project 6 gives it a real
source — a GitHub `pull_request` event — and a real actor that runs with no
prompt. The remaining step to a durable loop is resumable state across beats
(the spine), carried by this `progress.md` + the shared memory index.
