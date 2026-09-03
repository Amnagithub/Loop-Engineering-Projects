# Routine prompt — WRONG way: the secret lives in a `.env` file

> Trap prompt for the Secrets Drill. Locally this works — that is the trap.
> On a cloud Routine it fails, because a gitignored `.env` never reaches the
> clone the Routine runs on.

You are an automated one-shot routine. This task needs one secret: a dummy
token, `DUMMY_SECRET_TOKEN`.

## Goal
Prove you can obtain the secret and use it: run `task.py` in this folder.
On success it prints `SUCCESS` and writes `proof.json`.

## How to get the secret
1. The secret is stored in a file named `.env` in the same folder as this
   prompt (`drill/.env`).
2. Load that file into your shell environment so that `DUMMY_SECRET_TOKEN`
   becomes an environment variable. For example:

   ```bash
   set -a; source .env; set +a      # bash
   # or: python -m dotenv run python task.py
   ```

3. Run the task:
   ```bash
   python task.py
   ```
4. Definition of done: `task.py` prints `SUCCESS` and `proof.json` exists.

## Hard rule
If `.env` does not exist or cannot be read, STOP and report the failure
clearly. Do not improvise, do not hard-code the token, do not hunt for it
elsewhere.

## Why this is the WRONG pattern
A cloud Routine starts from a **fresh clone of your repo**. Git clones only
committed files, and `.env` is gitignored — so `.env` is never in that clone,
step 2 finds nothing, and the secret never arrives. It works on your machine
(where `.env` exists) and breaks only in the cloud, which makes it nasty to
diagnose.
