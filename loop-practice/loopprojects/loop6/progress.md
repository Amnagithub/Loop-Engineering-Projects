# Progress — Project 6 (Doorbell, event-driven)

## Start (2026-09-03)

- **Goal:** the reviewer must run on its own — a GitHub PR event (the doorbell)
  wakes it; no human prompt; it must flag the planted bug.
- Built the buggy module + contract (scaffold commit `b006014`):
  - `buggy.py` — `handle_all(events, handler)` with a planted **off-by-one**:
    iterating `events[:-1]` drops the **last** event and under-counts by one (a
    doorbell ring that goes unanswered).
  - `test_buggy.py` — `test_handle_all_delivers_every_event` (3 events → all 3
    delivered, count 3) fails against the bug. Verified with
    `C:\Python314\python.exe` (AssertionError → green after fix).
  - `skills/review-skill.md` — reviewer contract: dispatch spec, the bug class
    to hunt, run-the-tests verification, `VERDICT: FAIL/PASS`, read-only.
- **Environment notes:** `python`/`python3` on PATH are broken WindowsApps
  stubs; local interpreter `C:\Python314\python.exe`. Origin is one GitHub repo
  (`Amnagithub/Loop-Engineering-Projects`) holding loop1–6, so the Action lives
  at the repo root (`.github/workflows/doorbell-review.yml`).

## Doorbell wiring (on `main`)

`.github/workflows/doorbell-review.yml` fires on `pull_request` (opened /
reopened / synchronize) for `loop6/**` and: checks out the PR (Ring 1) runs the
suite; (Ring 2, gated on the `ANTHROPIC_API_KEY` secret) runs a headless Claude
Code review; (Ring 3) posts one automatic **🔔 Doorbell review** comment; (Ring
4) leaves a red check when the verdict is FAIL. The deterministic test review
needs no secret.

## Demo arrangement

`main` holds the **corrected** dispatcher (suite 2/2 green). The planted-bug
version lives on `doorbell/planted-bug`, so a PR from it into `main` carries the
bug as its diff.

## Gotcha recorded (important for the series)

`actions/checkout` on a `pull_request` checks out the **merge ref** (base +
head), not the raw head. A branch that merely *keeps* a buggy file that `main`
already fixed will silently resolve to `main`'s correct file — the CI shows PASS.
For a PR to *really contain* a bug in CI, the branch must change the file
relative to the shared ancestor (first demo run posted a spurious PASS for this
reason; fixing it meant merging `main` into the branch and re-introducing the
bug there). Lesson: demo a regression as an actual change on the branch, not as
an unchanged buggy baseline.

## Observed (2026-09-03) — the goal is met

Opened **PR #2** (`doorbell/planted-bug` → `main`, title "demo ring —
reintroduce the planted bug"). No prompt was typed. The workflow ran itself and
`github-actions[bot]` posted an automatic review: **`Verdict: FAIL`**, quoting
`test_buggy.py` line 12 (`AssertionError`: only 2 of 3 events delivered — the
last doorbell press dropped). Run conclusion: `failure` → red check on the PR.

## Remaining / next

- [ ] Add the `ANTHROPIC_API_KEY` repo secret (Settings → Secrets and variables
      → Actions) so Ring 2 posts the Claude Code prose review with the
      file:line finding; the deterministic FAIL already works without it.
- [ ] Close **PR #2 unmerged** — `main` is already correct; merging would
      reintroduce the bug.
- [ ] See the PASS direction: push the fix to that branch (`synchronize` re-rings
      the bell) and watch the automatic verdict flip to PASS; then merge.
- [ ] (Later) Widen the paths filter so the doorbell rings for every loop.

## Lesson being built toward

Project 5's missing piece was the **heartbeat**. Project 6 delivered it: a
GitHub `pull_request` event wakes a reviewer that runs and reports with no
prompt — demonstrated end-to-end on PR #2. The remaining step to a durable loop
is resumable state across beats (the spine), carried by this `progress.md` + the
shared memory index.
