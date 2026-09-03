# Routine prompt — RIGHT way: the secret comes from the environment

> Correct prompt for the Secrets Drill. Requires the secret to be configured
> in the platform's secret store (Routine env-var panel / GitHub Actions
> secret), where it is injected as an environment variable.

You are an automated one-shot routine. This task needs one secret: a dummy
token, `DUMMY_SECRET_TOKEN`.

**Credentials are available as environment variables; do not look for a .env file.**

## Goal
Prove you can obtain the secret and use it: run `task.py` in this folder.
On success it prints `SUCCESS` and writes `proof.json`.

## How to get the secret
1. The secret was configured in the platform's secret store for this run
   (the Routine env-var panel, or a GitHub Actions secret mapped into the
   step environment). It is ALREADY present in this session's environment as
   `DUMMY_SECRET_TOKEN`. Do not read any file.
2. Run the task:
   ```bash
   python task.py
   ```
3. Definition of done: `task.py` prints `SUCCESS` and `proof.json` exists.

## Hard rule
If `DUMMY_SECRET_TOKEN` is unset, STOP and report the failure clearly. Do not
improvise, do not hard-code the token, do not invent a `.env` file.

## Why this is the RIGHT pattern
The run's filesystem is a fresh clone of the repo, so **gitignored files such
as `.env` are never there** — a prompt that reads `.env` is guaranteed to fail
in the cloud. Environment variables, by contrast, are injected by the platform
*after* the clone, so they are the reliable channel for secrets. Saying the
credentials are in environment variables also stops the agent from burning
time hunting for (or accidentally committing) a `.env` file.
