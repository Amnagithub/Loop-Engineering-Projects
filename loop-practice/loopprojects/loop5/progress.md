# Progress — Project 5 (Codify the Body)

## Start (2026-09-03)

- Created `buggy.py` with two intentional bugs:
  - `attempts_remaining` — off-by-one (`max_attempts - used + 1`, extra `+1`).
  - `pass_rate` — returns a bare ratio instead of `* 100`.
- Created `test_buggy.py` with two tests that fail against `buggy.py`.
- Created `skills/fix-skill.md` with explicit PASS/FAIL criteria (what the fix
  may/must not do; FAIL if any test fails OR the test file is modified).
- Interpreter: `C:\Python314\python.exe` (`python`/`python3` are broken
  WindowsApps stubs on this machine).
- Next step: run the codified body in one go — for each candidate branch
  (implement a fix → independent reviewer replies only PASS/FAIL), collect the
  verdicts, merge only the PASS.

## Run — codified body executed in one go (2026-09-03)

Baseline committed on `main` (`8571beb`); both tests fail. Three candidate
branches were created off that buggy baseline; each was implemented, its tests
run, and an independent reviewer subagent (fresh context, read-only, may reply
only PASS or FAIL) gave a verdict:

| Candidate | What it did | Tests | Reviewer |
|---|---|---|---|
| `fix/loop5-clean` | fixed both bugs (`max_attempts - used`; `* 100`) | pass | **PASS** |
| `fix/loop5-half` | fixed `attempts_remaining` only | fail | **FAIL** |
| `fix/loop5-cheat` | rewrote test expectations; code unfixed | pass | **FAIL** |

Attempts used: **3 of 6** (limit respected). The gate has teeth: candidate C
made the suite green by editing tests, and the strict reviewer still returned
FAIL by checking the diff against the skill's "test file must not be modified"
rule — the reviewer is not just an echo of pytest.

Outcome: only candidate A was merged onto `main` (`--no-ff` merge). Final state
verified on `main`: tests 2/2 pass (`test_attempts_remaining`,
`test_pass_rate`); diff vs the buggy baseline is `buggy.py` only;
`test_buggy.py` was never touched on `main`.

## Why this run is still NOT a loop

**What the codified body does well:** it is a deterministic, self-contained
unit — problem (`buggy.py` + `test_buggy.py`) + contract
(`skills/fix-skill.md`) + one-shot execution that drafts, gates, and merges in
a single go with no step-by-step prompting, and leaves an auditable result
(verdict table + merge commit). Reusable: point it at a new buggy module +
skill and it re-runs the same body.

**Why it is still NOT a loop:** the engine ran exactly once and then stopped.
It does not re-enter itself, it holds no state between runs, and it never pulls
new work or re-checks an old goal unless a human types a new prompt. It is a
single-pass pipeline (draft → review → merge), not a loop.

**The two missing pieces that would turn it into a real loop:**
1. **Heartbeat** — a scheduler/timer that re-invokes the engine autonomously
   (cron, `/loop` interval, wake-up) so it fires again without a human prompt,
   keeps working across idle time, and can act on "nothing changed since last
   beat" or "candidate still failing".
2. **Spine / progress memory** — durable state (this `progress.md` plus a shared
   index such as `MEMORY.md`) recording the goal, current step, prior verdicts,
   and next action, so each heartbeat resumes from the checkpoint instead of
   restarting amnesiac. Without it every run forgets the previous one and
   cannot drive toward a goal that spans multiple beats.
