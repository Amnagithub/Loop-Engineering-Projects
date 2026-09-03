# Loop log — Project 11 (The Two-Routine Gate / Human Gate)

| Step | What happened | Result |
|------|---------------|--------|
| 1 | Designed the two-routine gate: A = draft only, human approves, B = action only via an API trigger; built on loop9 (transcript is truth) and loop10 (gitignored secret never reaches a Routine) | done |
| 2 | Wrote `gate.py` engine (draft / seal / approve / fire / serve / status / reset), `.gitignore` (ignores `.approval-token`), prompts `prompt-a.md` + `prompt-b.md`, loop11-local `run-routine.sh`, `README.md` | done |
| 3 | Ran run 01 end-to-end over the HTTP API: draft (no tag) → `/fire` before approval refused 403 → approve (token minted, gitignored) → `/fire` via curl → 200, tag `loop11/gate-01` → `/fire` again refused 409 `already_done` | done |
| 4 | Ran run 02 refusal paths: fire with wrong hash → 409 `hash_mismatch`; plan edited after approval → 409 `plan_changed`; then `reset --force` → PENDING | done |
| 5 | Captured proof under `results/demo/` (transcript/ledger events for both runs, reviewed plan, state at DONE, git-show proof, refusal map); wrote `progress.md` | done |
| 6 | Committed loop11 WITHOUT `.approval-token`; confirmed `git check-ignore` matches it | done |
