# Project 4 - Fix the bugs, then stop (maker-checker)

This project contains a `buggy.py` module with two intentional bugs and a
`test_buggy.py` suite that currently fails.

## Flow

**Implementer → Reviewer (PASS/FAIL) → Open PR only on PASS**

1. **Implementer** fixes the bugs in `buggy.py` using `skills/fix-skill.md`.
2. **Reviewer** checks the result against the skill's PASS/FAIL criteria and
   marks it PASS or FAIL.
3. Open a PR **only** if the review is PASS. On FAIL, go back to step 1.

## Files

- `buggy.py` - the functions to fix
- `test_buggy.py` - the tests that must pass
- `skills/fix-skill.md` - the skill describing the fix and its PASS/FAIL criteria
- `progress.md` - notes on current progress
- `loop-log.md` - log of each loop iteration (added once the loop runs)
