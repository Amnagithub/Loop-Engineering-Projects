# Routine prompt — ROUTINE B (ACTION ONLY) for the Two-Routine Gate

You are an automated one-shot routine, and you are the ACTION half of a
human gate. You are never scheduled and never self-starting: a human fires
you (via curl to the gate API, or by running this prompt with the approval
token injected) AFTER they have reviewed Routine A's plan. If any evidence
of that human approval is missing, you STOP — you do not act.

Work only inside this repository
(git root: `C:/Users/The-laptop-store/Documents/GitHub/Loop-Engineering-Projects`).
Do not touch files outside `loop-practice/loopprojects/loop11/`.

## Goal
Perform the ONE action described in the human-approved plan — create the
annotated git tag it proposes — and only that action, only once.

## Steps
1. Read `loop-practice/loopprojects/loop11/state.json`.
   - If `"phase"` is NOT `"APPROVED"`, STOP immediately and report:
     "no human approval — Routine B only acts after approve". Do not act.
2. The human must have injected the approval token as the environment
   variable `APPROVAL_TOKEN` when they fired you. If it is unset or empty,
   STOP and report: "approval token missing — a Routine fired without the
   human's token must not act". Do not read any file for it (the token
   never exists in the repo — that is the whole gate).
3. Read the plan file at the path in `state.json["plan_path"]` and confirm
   its sha256 still equals `state.json["plan_sha256"]`. If it differs, the
   plan changed after approval — STOP and report "plan changed after human
   approval". Do not execute an unreviewed plan.
4. Run the reviewed action through the gate engine, passing the approved
   hash and the token:
   ```
   python loop-practice/loopprojects/loop11/gate.py fire \
     <state.json plan_sha256> --token "$APPROVAL_TOKEN"
   ```
   The engine re-checks the phase, the token, the plan hash, and that the
   tag does not already exist, then creates exactly the tag from the plan
   metadata and appends a `B_acted` line to the ledger.
5. On success, print the tag name and tell the human to verify with
   `git show <tag>`. On any REFUSED output from the engine, STOP and report
   the refusal verbatim — do not try to bypass it.

## Hard rules
- You are ACTION ONLY: you act solely on the approved plan. Never improvise,
  never alter the message or tag, never create more than the one tag.
- Never push. Never run `git commit` or `git branch`.
- Single-fire: if the engine reports `already_done`, the tag exists — stop.
- Stop-and-report on every failure path above; a green exit is not success,
  the ledger + tag object are.

## Definition of done
- The annotated tag from the plan exists: `git tag --list '<plan tag>'`.
- The ledger has exactly one new `B_acted` event for this run, and its
  `token_fp` matches the approval the human minted.
- `state.json` has `"phase": "DONE"` and a `fired_at` timestamp.
