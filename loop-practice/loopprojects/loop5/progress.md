# Progress — Project 5 (Codify the Body)

## Start (2026-09-03)

- Created `buggy.py` with two intentional bugs:
  - `attempts_remaining` — off-by-one (`max_attempts - used + 1`, extra `+1`).
  - `pass_rate` — returns a bare ratio instead of `* 100`.
- Created `test_buggy.py` with two tests that fail against `buggy.py`.
- Created `skills/fix-skill.md` with explicit PASS/FAIL criteria (what the fix
  may/must not do; FAIL if any test fails OR the test file is modified).
- Interpreter: `C:\Python314\python.exe` (`python`/`python3` are broken
  WindowsApps stubs on this machine).
- Next step: run the codified body in one go — for each candidate branch
  (implement a fix → independent reviewer replies only PASS/FAIL), collect the
  verdicts, merge only the PASS.
