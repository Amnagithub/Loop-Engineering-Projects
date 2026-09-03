# Project 8 — Capstone: Your Own Daily Loop

A **daily debt scan** over the whole Loop-Engineering repo. Every morning a
fresh engine wakes with no memory, finds every whole-word
`TODO` / `FIXME` / `HACK` / `XXX` line, has an independent reviewer certify the
report, writes the accepted findings to the spine, and stops. One beat, fully
run, then silence until tomorrow's heartbeat.

The chore is loop3's original idea (a TODO scan) rebuilt with the **full
six-part machinery** the earlier projects earned piece by piece — spine memory,
a Maker-Checker gate, isolation, logging, measured cost, budget + escalation,
and a scheduler story. loop3 was the sketch; this is the capstone.

## One beat, end to end

> **heartbeat → fresh engine (no memory) reads `state.json` + `progress.md` →
> repo snapshot-isolated at HEAD → deterministic `scan.py` finds candidate
> lines (the "ring that never lies") → Maker drafts the triage report →
> Checker (strict, independent) returns PASS/FAIL → on PASS the findings land
> in the spine; on repeated FAIL the beat escalates to NEEDS_HUMAN → log + cost
> updated → beat stops.**

Each beat is driven by `loop.py`, a **deterministic Python orchestrator**. The
only AI is two *separate, fresh, headless* `claude -p` subprocesses (Maker then
Checker) — the same deployment shape Project 7 used, which is what makes the
per-run token cost **measured, not guessed** (see `runs/` + `cost.md`).

## The six parts (the checklist)

| Part | Where | How it is satisfied |
|------|-------|---------------------|
| **1. Folder structure** | `loop8/` | One folder per project; `skills/`, `runs/`, `state.json`, spine, log, cost all next to the driver. |
| **2. Spine** | `progress.md` + `state.json` | `progress.md` is *generated* from `state.json` each beat — Last Run / Findings / Already Reported / **Needs Human** sections; `state.json` is the machine truth. |
| **3. Skill files** | `skills/maker-skill.md`, `skills/checker-skill.md` | The two agent contracts: what the Implementer may write and how the Reviewer certifies it. |
| **4. Maker-Checker** | `loop.py` phases M + C | Implementer drafts; an **independent** fresh-context Reviewer re-derives every claim from the files and replies only `VERDICT: PASS|FAIL`. The orchestrator merges on PASS only. |
| **5. Isolation** | `loop.py` `git archive` snapshot | Agents work in a **throwaway snapshot of HEAD** in `%TEMP%`, never the live tree. A hash manifest proves the Maker touched no source. Optional `--no-isolation` for development. |
| **6. Logging + cost** | `loop-log.md`, `runs/`, `usage.csv`, `cost.md` | One log row per beat; every agent run's JSON + usage tokens preserved under `runs/`; `cost.md` regenerated from measured rows. |
| **7. Budget / guards** | `loop.py` `MAX_ATTEMPTS=3` | Each beat allows up to 3 Maker+Checker rounds. Exhaustion → `ESCALATED`, `State: NEEDS_HUMAN`; later beats **HOLD**. A Maker that edits sources → immediate **safety stop**. |
| **8. README** | this file | You are reading it. |

## Files

- `loop.py` — orchestrator (deterministic). Run one beat; see below.
- `scan.py` — deterministic scan: every whole-word tag line in the repo
  (skips `.git`, `__pycache__`, `runs/`, and the loop's own bookkeeping files).
  The ground truth both agents check against.
- `state.json` — machine state: run number, state flag, open markers, history.
- `progress.md` — the spine, regenerated from `state.json` each beat.
- `loop-log.md` — one row per beat (the heartbeat's paper trail).
- `cost.md` — measured tokens per beat and the monthly projection.
- `usage.csv` — raw measured rows (run, phase, attempt, tokens).
- `skills/maker-skill.md` — the Implementer contract (triage → draft JSON).
- `skills/checker-skill.md` — the strict Reviewer contract (verify → PASS/FAIL).
- `runs/` — per-agent-run JSON (`usage`), stderr, candidates, and the accepted
  draft for each beat.

## How to run a beat manually

Canonical interpreter is `C:\Python314\python.exe` (`python` on PATH is a
broken WindowsApps stub on this machine).

```powershell
# first time only — create state.json, progress.md, loop-log.md, cost.md
C:\Python314\python.exe loop.py --init

# run today's beat (snapshot-isolated; Maker + Checker; commits on PASS/ESCALATE)
C:\Python314\python.exe loop.py --date 2026-09-03

# inspect without spending tokens
C:\Python314\python.exe loop.py --check   # raw scan of the live tree
C:\Python314\python.exe loop.py --show    # current state.json

# after fixing whatever a human must fix
C:\Python314\python.exe loop.py --reset   # State: NEEDS_HUMAN -> RUNNING
```

Flags: `--date YYYY-MM-DD`, `--max-attempts N` (budget), `--no-isolation`
(agents work in the live tree — development only), `--no-commit`, `--claude
<path>`.

## The Maker-Checker flow (how a beat passes)

1. **Ground truth.** `scan.py` lists every candidate line. Deterministic,
   whole-word, so "TODOs" (prose) never matches — but prose that *spells* a
   whole word, and the tool's own definition files, still appear and must be
   triaged.
2. **Maker** reads each candidate + its context and classifies it **real debt**
   (a `# TODO` comment, a `- [ ] TODO:` item, a `// FIXME`) or **noise**
   (prose, examples, the scanner's own regex). It writes exactly one file: the
   draft JSON under `runs/`. It must cover every candidate — nothing dropped,
   nothing invented.
3. **Checker**, a *separate* fresh agent with no memory of the Maker's
   reasoning, re-opens every file and verifies: coverage is complete, each kept
   marker's `path:line:text` is verbatim, each excluded line really is noise,
   and NEW/EXISTING is right against `state.json`. It answers only
   `VERDICT: PASS` or `VERDICT: FAIL` + reasons.
4. **Orchestrator** merges the draft into `state.json`, regenerates the spine,
   appends the log + cost, and commits — *only on PASS*.

### Escalation (budget + Needs Human)

A loop that records a failure but never stops or pages anyone fails silently
forever (the lesson of Project 7). So: up to `MAX_ATTEMPTS=3` Maker+Checker
rounds per beat; if the Checker keeps failing, the beat writes a structured
**Needs Human** note (what / since / attempts / action / first thing to check),
sets `State: NEEDS_HUMAN`, and stops. Every later beat then **HOLDS** — it
burns no tokens and waits. A human fixes the cause, runs `--reset`, and the
loop resumes. A Maker that touches source files at all trips an immediate
safety-stop escalation.

## Isolation

The Maker and Checker never see your working tree. `loop.py` materialises
`git archive HEAD` into a throwaway `%TEMP%\loop8-beat-*` snapshot and runs the
agents there with `--permission-mode acceptEdits`; only the reviewed draft is
copied back. A SHA-1 manifest (taken after the candidates are written) is
re-hashed after the Maker runs — any change outside the loop8 `runs/` scratch
dir aborts the beat. The live tree only ever changes by the orchestrator's own
atomic commit of the reviewed result. (A `git worktree` would isolate the same
way; the snapshot is lighter and leaves no branches behind.)

## Cost awareness

Each beat runs **two** fresh `claude -p` agents (Maker + Checker), each paying
the ~18.5k-token harness overhead loop7 measured. Nominal beat ≈ 2 × 20k input
+ a few k output — a few dollars a month at reference rates, and the exact
numbers for *this* loop are measured in `cost.md` as beats accrue. A HOLD beat
costs ~0 (the orchestrator checks the flag and stops before waking any agent).
An escalated loop that stays scheduled still wastes the scheduler's wake — stop
the timer when `State: NEEDS_HUMAN`.

## Results (project executed 2026-09-03)

_(One real beat is run as part of this project's build — results, measured
cost, and lessons are appended here and in `progress.md` after the run.)_

## Run it unattended (next steps)

- **Claude Code `/loop`** — quickest for a supervised schedule: `/loop 24h
  C:\Python314\python.exe loop.py --date ...`. Claude wakes the beat for you.
- **Windows Task Scheduler** — a real daemon, no Claude session needed. Create a
  daily task at 07:00 running
  `C:\Python314\python.exe C:\...\loop-practice\loopprojects\loop8\loop.py`
  (start in the `loop8` folder), then add a second daily task that checks
  `state.json` and stops itself if `"state": "NEEDS_HUMAN"` (Project 7's
  finding: stop the scheduler, not just the beat).
- **GitHub Actions cron** — if this repo lives on GitHub, add a
  `schedule: [cron: "0 7 * * *"]` workflow (see the sibling
  `.github/workflows/doorbell-review.yml` from Project 6) that checks out,
  installs Claude Code, sets `ANTHROPIC_API_KEY`/`ANTHROPIC_BASE_URL` secrets,
  runs `loop.py`, and commits the beat back.

Each beat is one atomic commit, so history itself is the audit: read `git log`
for the loop8 folder to replay every morning.
