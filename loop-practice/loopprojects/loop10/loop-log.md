# Loop log — Project 10 (The Secrets Drill)

| Step | What happened | Result |
|------|---------------|--------|
| 1 | Designed drill: 3 arms (local `.env` / cloud clone / cloud clone + env var) around one task needing `DUMMY_SECRET_TOKEN` | done |
| 2 | Created `.gitignore` (`.env`, `.drill-clone/`), `drill/.env` (dummy token), `.env.example`, `task.py`, `run-drill.py`, two prompts | done |
| 3 | Wrote `README.md`, `progress.md`, `loop-log.md` | done |
| 4 | Confirmed `git check-ignore -v drill/.env` matches; committed loop10 WITHOUT `.env` | done |
| 5 | Ran full drill: local SUCCESS, cloud FAIL (.env absent in clone), panel SUCCESS; `DRILL PASS` | done |
| 6 | Ran failing version alone (`cloud`, exit 1) and successful version alone (`panel`, exit 0) | done |
