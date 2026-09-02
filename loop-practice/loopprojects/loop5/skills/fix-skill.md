---
name: fix-skill
description: Use when fixing the two intentional bugs in Project 5's buggy.py so that every test in test_buggy.py passes. Applies to the codified draft-and-review body (candidate fix -> independent reviewer) in the loop-practice repo.
---

# Fix the Buggy Module (Project 5)

## Goal

Make the tests in `test_buggy.py` pass by fixing the two intentional bugs in
`buggy.py`. Do exactly that, nothing more.

## What the fix SHOULD do

- `attempts_remaining(max_attempts, used)` returns `max_attempts - used`
  (drop the stray `+ 1`).
- `pass_rate(passed, total)` returns the percentage, i.e. `passed / total * 100`.
- Change only the buggy lines. Keep function names, signatures, and module
  structure intact.

## What the fix must NOT do

- Do **NOT** modify `test_buggy.py`, add tests, or remove tests.
- Do **NOT** rename, remove, or reorder the functions.
- Do **NOT** change any other behavior or add new features/refactors.

## PASS / FAIL criteria

- **PASS:** Running the test file (`python test_buggy.py`) reports all 2 tests
  passing (`test_attempts_remaining`, `test_pass_rate`).
- **PASS:** `attempts_remaining(6, 2) == 4` and `pass_rate(3, 4) == 75.0`.
- **FAIL:** Any test fails or errors.
- **FAIL:** The test file was modified.
