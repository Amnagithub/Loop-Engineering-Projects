---
name: fix-skill
description: Use when fixing the intentional bugs in Project 4's buggy.py so that every test in test_buggy.py passes. Applies to the maker-checker flow in the loop-practice repo.
---

# Fix the Buggy Module

## Goal

Make the tests in `test_buggy.py` pass by fixing the intentional bugs in
`buggy.py`. Do exactly that, nothing more.

## What the fix SHOULD do

- `calculate_total(price, quantity)` returns `price * quantity`.
- `countdown(n)` returns `[n, n-1, ..., 1, 0]` — inclusive of `0`.
- Change only the buggy lines. Keep function names, signatures, and module
  structure intact.

## What the fix must NOT do

- Do **NOT** modify `test_buggy.py`, add tests, or remove tests.
- Do **NOT** rename, remove, or reorder the functions.
- Do **NOT** change any other behavior or add new features/refactors.

## PASS / FAIL criteria

- **PASS:** Running `python test_buggy.py` reports all 2 tests passing
  (`test_calculate_total`, `test_countdown`).
- **PASS:** `calculate_total(5, 3) == 15` and `countdown(3) == [3, 2, 1, 0]`.
- **FAIL:** Any test fails or errors.
- **FAIL:** The test file was modified.
