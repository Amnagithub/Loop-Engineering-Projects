# Project 12 — The Dreaming Loop (Final Capstone)

The **meta-loop**: the loop that reads the other loops' dated logs and
proposes changes to the *shared rules they all follow*. Most loops act on the
repo; the dreaming loop acts on **the rules of the act**. Once a day it wakes,
dreams over everything that happened since its last dream, and asks: *is
there a failure or correction that keeps happening? What is the smallest rule
that would stop it — and what rule is dead weight we can delete?*

It never changes the rules itself. A dreaming beat ends with a **pull request
on a `claude/dream-<N>` branch** — never a commit to `main`, never a push.
Nothing in the shared rules changes without a human merging the PR.

Status: **done** — one full dreaming beat ran with real headless agents; it
caught the deliberately planted repeated failure and turned it into a
branch-held proposal (see `proposals/`, `runs/`, `loop-log.md`).

## The lesson in one sentence

When a correction keeps reappearing across your loops, the fix is not to
correct it again — it is to **raise it once into a shared rule**, and to prune
the rules that are dead weight — but a loop that edits its own rules is a loop
that can drift, so the change goes on a `claude/dream-<N>` branch and only a
**human merge** lands it. A dreaming loop that cannot propose a deletion is
only half a dream.

## One beat, end to end

> **heartbeat → fresh engine reads `dreaming-state.md` → deterministic
> `scan.py` proves which failure/correction signatures appear more than once
> in the loops' dated logs (the ring that never lies) → snapshot of HEAD →
> DREAMER (fresh headless Claude) drafts the smallest rule/skill improvement +
> one deletion, citing real records → CHECKER (fresh headless Claude)
> re-derives every citation → on PASS the proposal + PR body are committed to
> a local `claude/dream-<N>` branch → `dreaming-state.md` advances → the beat
> prints the exact `git push` + `gh pr create` one-liner for a human.**

The Dreamer never edits the repo (it writes one proposal file, loop8-style),
and the rules corpus it may touch is exactly one folder:
`loopprojects/skills/`.

## The three requirements a proposal must satisfy

1. **Evidence, not guesses.** Every proposal rests on records the deterministic
   scanner (and then the Checker) can cite verbatim — `file`, `line`, `date`,
   run — and a failure must appear in **two or more distinct dated records**.
2. **Smallest possible.** One new small rule file, or a one-section addition to
   one existing rule. A conventions essay is a fail.
3. **A deletion, too.** Each dream also names one dead rule (a placeholder
   stub, something superseded) with the check that proved it dead.

Rule changes are gated like loop11's human gate, but for the whole practice:
**Routine A** (this loop) drafts and proposes; **the human** reviews and merges
the branch. The dreaming engine is *structurally* unable to land a rule — it
returns to `main` with the rule files untouched.

## What was planted (be transparent about the drill)

Project 12's demo runs against a **drill input fixture**: `observed-runs.md`,
a dated fleet log that stands in for "the loops' own recent logs." Its rows
`5` and `6` are the **deliberately planted repeated failure** — the same stall
on the same date, so the scanner must find a signature that appears twice. The
real repeats already in the corpus (e.g. the interpreter correction in
loop5/6/8/10/11 progress files) are the same *shape* of evidence; the fixture
just makes the demo deterministic. A production deployment would point
`scan.py` at the live loops' logs and delete the fixture.

## Files

```
loop12/
  dreaming-state.md         the spine: last dreaming date, run, state, ledger
  scan.py                   deterministic evidence scanner (the never-lies ring)
  dream.py                  the orchestrator (run one beat)
  observed-runs.md          the drill input fixture (planted repeat lives here)
  skills/
    dreamer-skill.md        the Dreamer contract (propose -> one JSON, cite real)
    checker-skill.md        the strict Checker contract (re-derive -> PASS/FAIL)
  proposals/claude/dream-N/ what the beat committed to its branch: proposal.json,
                            PR.md (the pull-request body a human reviews)
  runs/dream-N/             per-beat artifacts: scan.json, agent JSONs, proposal
  progress.md / loop-log.md / cost.md / usage.csv   generated paper trail
  .gitignore                .loop12-beats + __pycache__ ignored
```

## Exact steps (run from the git repo root, interpreter `C:/Python314/python.exe`)

```bash
# 1. one full dreaming beat for a date
C:/Python314/python.exe loop-practice/loopprojects/loop12/dream.py --date 2026-09-03

# 2. see the proposal the beat committed to its branch
git diff main..claude/dream-1 --stat
cat  loop-practice/loopprojects/loop12/proposals/claude/dream-1/PR.md

# 3. the rules on main are UNCHANGED until you merge the branch
git branch --list 'claude/*'        # the proposal branch exists
git log main --oneline -1           # main untouched by the dream

# 4. review, then (only you) open / merge the pull request
git push -u origin claude/dream-1
gh pr create --base main --head claude/dream-1 \
  --title '<the dream title>' --body-file \
  loop-practice/loopprojects/loop12/proposals/claude/dream-1/PR.md

# 5. commit the dreaming loop's own bookkeeping on main (state/log/progress)
git add loop-practice/loopprojects/loop12
git commit -m "loop12: dream 1 — <title>"
```

While a `claude/dream-<N>` proposal is open the loop **HOLDs** (it will not
dream the same window twice). After you merge or delete the branch, clear the
gate with `dream.py --reset`. If the Checker never passes after `--max-attempts`
rounds, the beat **ESCALATES** to `NEEDS_HUMAN` and later beats HOLD.

## Rehearsal / check commands

```bash
# run only the deterministic scan (no agents, no branch) for the window since
# the last dream, up to a date:
C:/Python314/python.exe loop-practice/loopprojects/loop12/dream.py --check --date 2026-09-03

C:/Python314/python.exe loop-practice/loopprojects/loop12/dream.py --show    # state
C:/Python314/python.exe loop-practice/loopprojects/loop12/dream.py --reset   # clear NEEDS_HUMAN
```

## How this inherits the practice

- **loop8** gives the architecture: deterministic scanner + isolated snapshot
  + fresh headless Maker/Checker + measured cost (`cost.md`).
- **loop11** gives the gate: split so the loop *drafts* and a human *merges*;
  the dream engine never commits rules to `main` and never pushes.
- **loop9** gives the lesson the Checker enforces: a status line is coarse —
  the **citations are the truth** (every one re-derived from the files).
- **loop6/7** give the ring: the scanner only reports what it can cite
  verbatim, and budget exhaustion escalates to a human instead of failing
  silently.
- **loop10** gives the invariant: secrets (here, the human's approval to land
  a rule) never live where a loop could reach them — they are a human merge.

## Security / guardrails

- The dreaming loop's blast radius on the branch is one folder:
  `loopprojects/skills/`. `dream.py` refuses proposal paths outside it.
- Rule changes exist only on `claude/dream-<N>`. The engine checks out of the
  branch and returns to `main`; it prints (never runs) the push + `gh pr
  create` one-liner.
- `main` rule files are byte-identical before and after a beat — verify with
  `git diff --stat main..HEAD` before merging anything.
