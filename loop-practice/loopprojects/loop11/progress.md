# Progress — Project 11 (The Two-Routine Gate / Human Gate)

## Start (2026-09-03)

- Goal: build the complete two-routine human gate — Routine A drafts a
  reviewable action, a human approves, Routine B performs one small action
  only when fired through an API trigger (curl). Done when: B runs only after
  a manual trigger, the action is visible in a transcript, the pattern is
  documented.
- Designed the gate around the repo's accumulated lessons:
  - loop9: a Routine shows a coarse status; the full transcript is truth.
  - loop10: a gitignored file never reaches a Routine's clone — the gate's
    approval token is gitignored, so nothing a Routine can read can fire B.
- Pattern: split, don't rely on promises. Routine A is structurally DRAFT
  ONLY; the irreversible step (one annotated git tag, which cannot be
  duplicated → single-fire by construction) lives behind `POST /fire`, which
  refuses unless the state is APPROVED, the caller proves a token minted at
  approve time (stored only in gitignored `.approval-token`), and the plan
  file still hashes to the approved value.
- Created: `gate.py` (engine: draft / seal / approve / fire / serve / status /
  reset + local API), `.gitignore`, `state.json`, `ledger.jsonl`,
  `routine/prompt-a.md`, `routine/prompt-b.md`, `routine/run-routine.sh`,
  `README.md`, `loop-log.md`.
- Next: run one real end-to-end cycle (draft → pre-approval refusal → approve
  → curl fire → tag → re-fire refusal), capture it under `results/`, then
  commit (never the `.approval-token`).

## Done ✅ (2026-09-03)

- Ran a real cycle with `C:/Python314/python.exe`:
  - `gate.py draft` → wrote `runs/01/plan.md`, phase `AWAITING_REVIEW`, no tag.
  - `curl /fire` before approval → HTTP 403 `no_approval` (refusal logged).
  - `gate.py approve` → minted token (gitignored), phase `APPROVED`.
  - `curl /fire` with the printed token + hash → HTTP 200; annotated tag
    `loop11/gate-01` created at HEAD; ledger `B_acted`; phase `DONE`.
  - `curl /fire` again → HTTP 409 `already_done`; no second tag.
  - Second cycle (run 02): approved, then fired with a wrong hash → 409
    `hash_mismatch`; edited the plan → 409 `plan_changed`; reset → PENDING.
- Proof captured under `results/demo/`: the full transcript (ledger events
  for both runs), the reviewed plan, state at DONE, git-show proof, and every
  refusal path. `git tag -l` shows `loop11/gate-01` and `loop11/gate-02`.
- Lesson recorded: the human gate is structural — split the routine so the
  action is only reachable through an approval token that never enters the
  repo, and lock Routine B to the exact reviewed plan by hash.
