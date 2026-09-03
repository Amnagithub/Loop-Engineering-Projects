# Project 11 — The Two-Routine Gate (Human Gate)

Goal: learn how to keep an irreversible action behind a human. The gate
splits the work into two routines — **Routine A drafts, a human reviews,
Routine B acts — and Routine B is *structurally* unable to act until the
human fires it.** The drill runs the whole pattern deterministically and for
free (a tiny local API + `curl`), and ships the two Routine prompts for real
use.

Status: **done** — the gate engine is deterministic and re-runnable, a real
end-to-end run (approve → fire → annotated tag) is captured under
`results/demo/`, and the two Routine-ready prompts are included.

## The lesson in one sentence

If you never want an autonomous routine to take an irreversible action, do
not rely on it promising not to — **split the task**: give Routine A only the
*draft* step (it is structurally incapable of the action), and keep the
*approve → act* step behind a one-time token that exists only in the human's
hands. The token is minted at approve time and written to a **gitignored
file**, so a Routine (which starts from a committed clone) can never read it
and can never approve itself — the loop10 secret rule, applied to the gate.

## The two routines

| Routine | Role | Can it take the action? | How it starts |
|---------|------|--------------------------|---------------|
| **A — Draft only** | Inspects the repo, writes a reviewable **plan** (propose one annotated git tag + release note on a pinned commit), seals state to `AWAITING_REVIEW`, leaves a note for the human | **No.** Its prompt and tool scope forbid `git tag`/`commit`/`push`; the engine's `draft`/`seal` only ever write plan + state files | Scheduled / one-off (runs unattended) |
| **HUMAN** | Reads the plan, runs `approve` → mints a one-time approval token (gitignored) | The *only* actor who can make the gate fire | You, deliberately |
| **B — Action only** | Reads the approved plan and creates **exactly that one tag**, once | Yes — but only after it verifies: phase `APPROVED` **and** the caller proves the token **and** the plan file still hashes to the approved value | Fired by you via `POST /fire` (`curl`) |

The "action" in this drill is creating an **annotated git tag** on the shared
repo. Tags cannot be duplicated, so single-fire is structural, and the tag
object is durable proof. (Locally a tag is easy to delete with `git tag -d`,
so the drill is safe — but it is still a real, human-gated repo mutation.)

## What makes Routine B un-fireable without you

Three independent checks run on **every** fire attempt, and every attempt —
success *and* refusal — is appended to `ledger.jsonl`, the gate's transcript:

1. **No schedule / no self-start.** Routine B is never scheduled. The only
   caller is the API endpoint, and the only endpoint that runs the action is
   `POST /fire`.
2. **The approval token is not in the repo.** `approve` mints a random token
   into `.approval-token`, which is gitignored. A Routine runs on a committed
   clone → the file is never there (loop10) → nothing a routine can read lets
   it fire B. The token is your signature; you carry it from `approve` to the
   `curl`.
3. **The plan is hash-locked.** Routine B only executes a plan whose sha256
   equals the value the human approved *and* whose file is byte-identical to
   what it was at approve time. Edit the plan after approving and B refuses —
   it will never run a command the human did not review.

A `200` from `/fire` is *not* the proof. The proof is the `B_acted` line in
the ledger **and** the tag object (`git show <tag>`) — the loop9 lesson: the
status is coarse, the transcript is truth.

## Files

```
loop11/
  .gitignore                  .approval-token + __pycache__ ignored
  gate.py                     the whole gate engine: draft / seal / approve /
                              fire / serve / status / reset + the local API
  state.json                  the gate state (phase, plan hash, tag, ...)
  ledger.jsonl                append-only transcript of every event
  runs/01/plan.md             the plan a real run produced (reviewed artifact)
  routine/
    prompt-a.md               Routine A prompt (DRAFT ONLY, self-contained)
    prompt-b.md               Routine B prompt (ACTION ONLY, self-contained)
    run-routine.sh            loop9-style harness to rehearse either prompt
  results/demo/               the executed demo, frozen: transcript (ledger),
                              the reviewed plan, state at DONE, git-show proof
```

## Exact steps

Everything below runs from the **git repo root**
(`C:/Users/The-laptop-store/Documents/GitHub/Loop-Engineering-Projects`).
Use the real interpreter `C:/Python314/python.exe`. `curl` is `curl.exe` on
Windows; the single-quoted JSON works in git-bash and PowerShell.

### 0. (Optional) Start the API — the trigger Routine B is fired through

```bash
C:/Python314/python.exe loop-practice/loopprojects/loop11/gate.py serve
# -> Human-gate API listening on http://127.0.0.1:8787
```

If you skip this, the equivalent CLI form of every fire below is printed by
`approve` (same checks, same code path).

### 1. Run Routine A — one-off, draft only

```bash
C:/Python314/python.exe loop-practice/loopprojects/loop11/gate.py draft
```

Expect: `plan written: loop11/runs/<RUN>/plan.md`, phase `AWAITING_REVIEW`,
and a note to the human. **No tag was created** — check:
`git tag --list 'loop11/gate-<RUN>'` is empty.

### 2. Review the draft yourself

```bash
cat loop-practice/loopprojects/loop11/runs/<RUN>/plan.md
```

Read: the exact `git tag` command Routine B would run, the message it would
attach, the pinned commit. Nothing has executed.

### 3. (Optional but convincing) Try to fire Routine B *before* you approve

```bash
curl -s -X POST http://127.0.0.1:8787/fire \
  -H 'Content-Type: application/json' \
  -d '{"token":"not-the-real-token","plan_sha256":"anything"}'
# -> {"ok": false, "reason": "no_approval", ...}   (HTTP 403)
```

Routine B refuses — there is no approval yet. The refusal is in the ledger.

### 4. Manually approve

```bash
C:/Python314/python.exe loop-practice/loopprojects/loop11/gate.py approve
```

This mints the one-time approval token (gitignored) and prints the **exact
curl** to fire Routine B, with the token and plan hash already filled in.
Copy it.

### 5. Fire Routine B — the API trigger

Run the curl `approve` printed (same shape as):

```bash
curl -s -X POST http://127.0.0.1:8787/fire \
  -H 'Content-Type: application/json' \
  -d '{"token":"<the token approve printed>","plan_sha256":"<the approved hash>"}'
# -> {"ok": true, "tag": "loop11/gate-<RUN>", ...}
```

### 6. Verify B only ran because of your approval

```bash
git tag -l 'loop11/*'                        # the tag exists
git show loop11/gate-<RUN>                   # the reviewed message is attached
cat loop-practice/loopprojects/loop11/ledger.jsonl | tail -8
```

The ledger shows exactly: one `A_drafted`, one `human_approved`, then one
`B_acted` with the token fingerprint that matches your approval. Fire again:

```bash
curl -s -X POST http://127.0.0.1:8787/fire \
  -H 'Content-Type: application/json' \
  -d '{"token":"<same token>","plan_sha256":"<same hash>"}'
# -> {"ok": false, "reason": "already_done", ...}   (HTTP 409)
```

No second tag. **The action happened once, and only after you approved.**

## Optional: prove the plan is hash-locked

Approve a plan, then edit one word of
`loop11/runs/<RUN>/plan.md`, and fire B with the *approved* hash:

```bash
curl -s -X POST http://127.0.0.1:8787/fire \
  -H 'Content-Type: application/json' \
  -d '{"token":"<token>","plan_sha256":"<approved hash>"}'
# -> {"ok": false, "reason": "plan_changed", ...}   (HTTP 409)
```

Routine B refuses to execute a plan that no longer matches what you approved.
Reset afterwards: `python loop11/gate.py reset --force`.

## Re-running / starting a fresh cycle

Each `draft` picks the next run number and proposes `loop11/gate-<RUN>`, so
cycles accumulate (`runs/01`, tag `gate-01`, then `runs/02`, `gate-02`, ...).
Tags left behind are durable proof and can be deleted locally with
`git tag -d loop11/gate-<RUN>`. `reset --force` returns the gate to `PENDING`
and deletes the approval token.

## Optional: rehearse the prompts as real Routines

The engine above is the deterministic, free stand-in (same split, same
checks). To see the two *prompts* run as real unattended routines, use the
loop9-style harness in `routine/`:

```bash
# Routine A drafts + seals a plan (a real routine, costs ~$0.20)
bash loop-practice/loopprojects/loop11/routine/run-routine.sh \
  loop-practice/loopprojects/loop11/routine/prompt-a.md 01-a-draft

# review runs/<next>/plan.md, then approve ...
C:/Python314/python.exe loop-practice/loopprojects/loop11/gate.py approve

# ... and fire Routine B as a real routine, injecting the human's token
APPROVAL_TOKEN=<token from approve> \
bash loop-practice/loopprojects/loop11/routine/run-routine.sh \
  loop-practice/loopprojects/loop11/routine/prompt-b.md 02-b-act
```

Each run saves `STATUS.json` + the full `transcript.jsonl` under
`routine/results/runs/`. Note the loop9 lesson again: even Routine B's green
status is not the proof — read its transcript, then confirm the ledger line
and the tag object. (The cloud `/schedule` feature needs a claude.ai OAuth
login, which this machine does not have — see `loop9/README.md`. On a
subscribed account these two prompts drop straight into real Routines: A
scheduled, B never scheduled, only ever run from the web/CLI by you.)

## Security notes

- The approval token is a **demo credential** minted per-approval and stored
  in a gitignored file on your machine. In production, keep it in a secret
  store / SSO so only the human can obtain it, and never print it to logs.
- The token never enters the repo: it cannot be committed (gitignored) and a
  Routine clone therefore never has it — that property, not politeness, is
  what makes the gate hold.
- The tagged commit is whatever HEAD was at draft time; the tag itself is a
  normal local annotated tag (delete with `git tag -d`). Nothing here pushes.
