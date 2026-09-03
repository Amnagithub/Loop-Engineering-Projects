# results/demo — an executed Two-Routine Gate

This folder is a snapshot of one real end-to-end run of the loop11 gate on
this machine (2026-09-03), kept as durable proof that the pattern works. The
live gate files (`state.json`, `ledger.jsonl`, `runs/`) are the working copy;
this folder is the frozen record.

## What happened (two cycles)

**Run 01 — the happy path, and the gate visibly closed both sides:**
1. Routine A drafted `runs/01/plan.md` (propose annotated tag
   `loop11/gate-01` at HEAD). No tag created.
2. A fire attempt *before* approval → `HTTP 403 no_approval`.
3. Human ran `approve` → one-time token minted (gitignored).
4. Human fired Routine B with `curl` + the token → `HTTP 200`, tag
   `loop11/gate-01` created with the exact reviewed message.
5. A second fire → `HTTP 409 already_done`. No duplicate tag.

**Run 02 — the hash locks prove Routine B runs only the reviewed plan:**
1. Routine A drafted `runs/02/plan.md`; human approved.
2. Fire with a *wrong* plan hash → `HTTP 409 hash_mismatch`.
3. Plan file edited after approval, then fired with the *approved* hash →
   `HTTP 409 plan_changed` — B refuses to execute an unreviewed plan.
4. Plan restored to the approved bytes and fired → `HTTP 200`, tag
   `loop11/gate-02`.

## Files

- `transcript.jsonl` — the ledger, verbatim: every draft, approval, action,
  and refusal in order. This is the transcript that is truth (the loop9
  lesson) — not the HTTP 200s.
- `plan.md` — the exact plan a human reviewed and approved for run 01.
- `state-final.json` — the gate state at the end (`phase: DONE`, run 02).
- `proof.txt` — tag list, the tag message, the transcript, and how each
  refusal reads over the API.

## Verify it yourself

```bash
git tag --list 'loop11/*'                     # loop11/gate-01 and gate-02 exist
git show loop11/gate-01                        # message == the reviewed plan.md
git show loop11/gate-02
cat loop-practice/loopprojects/loop11/results/demo/transcript.jsonl
```

Only two `B_acted` lines exist — one per cycle — and each is preceded in the
ledger by the `human_approved` event whose `token_fp` it shares. The tags are
the machine-readable residue of those approvals.
