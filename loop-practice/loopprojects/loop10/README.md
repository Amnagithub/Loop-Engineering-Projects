# Project 10 — The Secrets Drill

Goal: learn the one rule that decides whether a Routine/cloud agent can ever
see a secret — **gitignored files never reach the cloud clone**. The drill
builds a tiny one-secret task and runs it in three environments so you can
*see* the `.env` version work locally, break in a simulated cloud clone, and
succeed again once the secret arrives as an environment variable.

Status: **done** — the harness is deterministic, free to re-run, and the two
Routine-ready prompts are included.

## The lesson in one sentence

A Routine (or any cloud run) starts from a **fresh clone of your repo**. Git
clones only committed files. A secret stored in `.env` — which should be
gitignored — is therefore **never in that clone**, so any prompt that reads
`.env` is guaranteed to fail in the cloud, even though it works perfectly on
your machine. The correct channel is an **environment variable**, injected by
the platform (Routine env-var panel / GitHub Actions secret) *after* the
clone happens.

## The three environments the drill runs

| Arm | Environment | How the secret is delivered | Result |
|-----|-------------|------------------------------|--------|
| 1 `local` | your real checkout (`.env` present) | read `.env`, export, run task | **SUCCESS** — the trap: it works here |
| 2 `cloud` | simulated cloud clone (only git-tracked files; gitignored `.env` is absent) | try to read `.env` … | **FAIL** — this is the `.env` version failing in the cloud |
| 3 `panel` | same cloud clone | secret injected as an environment variable | **SUCCESS** — the correct way |

The "cloud clone" in arm 2/3 is not faked with heuristics: the drill asks git
which files a clone would contain (`git ls-files`), copies exactly those into
a scratch folder, and runs the task there. `.env` is gitignored, so it is not
in that list — mechanically identical to what a Routine sees.

## Files

```
loop10/
  .gitignore                .env + scratch (.drill-clone) are ignored
  README.md                 this file
  progress.md               write-up / state
  loop-log.md               per-step log
  drill/
    .env                    the WRONG-way secret file (DUMMY ONLY, never committed)
    .env.example            tracked reference copy of the variable
    task.py                 the task: reads DUMMY_SECRET_TOKEN from the environment,
                            HMAC-signs a probe, writes proof.json
    run-drill.py            the 3-arm deterministic harness
    prompt-env-file.md      WRONG routine prompt: "read the secret from .env"
    prompt-env-var.md       RIGHT routine prompt: carries the line
                            "Credentials are available as environment variables;
                            do not look for a .env file."
```

## Exact steps

Everything below runs from the **git repo root**
(`C:/Users/The-laptop-store/Documents/GitHub/Loop-Engineering-Projects`).
On this machine `python` may be a broken WindowsApps stub — use the real
interpreter `C:/Python314/python.exe` (the drill re-uses your interpreter for
children automatically).

### 0. Confirm the `.env` is gitignored (the whole mechanism in one command)

```bash
git check-ignore -v loop-practice/loopprojects/loop10/drill/.env
# -> loop10/.gitignore:2:.env    loop-practice/loopprojects/loop10/drill/.env
```

That rule is why the file never reaches a clone.

### 1. Commit the drill (NOT the `.env`)

A simulated cloud clone only contains **committed** files, so commit first:

```bash
git add loop-practice/loopprojects/loop10
git commit -m "loop10: secrets drill - .env vs env var, 3-arm harness"
git status --porcelain            # confirms drill/.env is NOT listed
```

### 2. Run the whole drill — all three arms side by side

```bash
C:/Python314/python.exe loop-practice/loopprojects/loop10/drill/run-drill.py
```

Expect: arm 1 `SUCCESS`, arm 2 `FAIL` (`.env` absent in the clone), arm 3
`SUCCESS`, and a final `DRILL PASS` line.

### 3. Run the FAILING version on its own (the `.env` route in a cloud clone)

```bash
C:/Python314/python.exe loop-practice/loopprojects/loop10/drill/run-drill.py cloud
```

This is the `prompt-env-file.md` behaviour. It exits `1` on purpose — the
failure is the result you asked to see.

### 4. Run the SUCCESSFUL version on its own (secret from the environment)

```bash
C:/Python314/python.exe loop-practice/loopprojects/loop10/drill/run-drill.py panel
```

This is the `prompt-env-var.md` behaviour. Exits `0`.

### 5. Optional: the trap, live

```bash
C:/Python314/python.exe loop-practice/loopprojects/loop10/drill/run-drill.py local
```

Works — because `.env` is sitting right there. This is why the bug hides until
the code runs somewhere that clones the repo.

## The correct way to provide a secret

Do not ship `.env`. Put the value in the platform's secret store and let it
arrive as an environment variable:

- **GitHub Actions** — repo → *Settings → Secrets and variables → Actions →
  New repository secret*: name `DUMMY_SECRET_TOKEN`, value the token. Then map
  it into a step with `env: { DUMMY_SECRET_TOKEN: ${{ secrets.DUMMY_SECRET_TOKEN }} }`.
- **Claude Routine / cloud runs** — the Routine's env/secret configuration
  (the same mechanism the GitHub repo secret gate uses). The value is injected
  into the run's process environment.

And the prompt must say it, so the agent does not hunt for a file:

> Credentials are available as environment variables; do not look for a .env file.

That line is the first content rule of `drill/prompt-env-var.md`.

## What a real Routine run would show

Rehearse either prompt exactly as loop9 did (fresh headless session, capture
the full transcript): run `prompt-env-file.md` in a context that only has
committed files and you get a clean stop-and-report failure — no token, no
`proof.json`. Run `prompt-env-var.md` with `DUMMY_SECRET_TOKEN` injected and
the same task succeeds. The cloud `/schedule` feature itself is not reachable
on this machine (it needs a claude.ai OAuth login — see `loop9/README.md`),
so the deterministic harness above is the faithful, free stand-in.

## Security notes

- Everything here is a **dummy token** (`DUMMY_SECRET_TOKEN_12345`). Never
  rehearse this with a real credential — a real secret in `.env` would sit in
  your working tree and could be committed or exfiltrated by a tool run.
- `task.py` never prints the full value, only a masked key id; keep that habit.
- If `.env` is ever committed by accident, rotate the value and purge it from
  history — presence in git history outlives deleting the file.
