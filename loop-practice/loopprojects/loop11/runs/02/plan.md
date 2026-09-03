# Gate plan - run 02   (HUMAN REVIEW REQUIRED - nothing has run yet)

Prepared by: Routine A (draft only) at 2026-09-03T07:27:06+00:00
Repo: loop-practice/loopprojects/loop11
Target commit: 654e281d6e20661020384a483da59b31986892b0  (loop10: fix single-arm exit codes in the drill harness)
Phase: AWAITING_REVIEW

<!-- gate-metadata -->
{
  "tag": "loop11/gate-02",
  "target": "654e281d6e20661020384a483da59b31986892b0",
  "message": "loop11/gate-02: approve Project 11 gate run 02\n\nThis annotated tag marks commit 654e281d6e20 (loop10: fix single-arm exit codes in the drill harness) as the\nrelease point for Project 11 (Two-Routine Gate). Routine A drafted\nthis plan; a human reviewed it and fired Routine B to create the tag.\nThe tag is the machine-readable proof the gate held: Routine B ran\nexactly once, only after human approval."
}
<!-- /gate-metadata -->

## Proposed action (ONE irreversible step)

Create the annotated git tag `loop11/gate-02` at commit `654e281d6e20661020384a483da59b31986892b0`:

    git tag -a loop11/gate-02 654e281d6e20661020384a483da59b31986892b0 -m "<message below>"

## Message Routine B will attach

loop11/gate-02: approve Project 11 gate run 02

This annotated tag marks commit 654e281d6e20 (loop10: fix single-arm exit codes in the drill harness) as the
release point for Project 11 (Two-Routine Gate). Routine A drafted
this plan; a human reviewed it and fired Routine B to create the tag.
The tag is the machine-readable proof the gate held: Routine B ran
exactly once, only after human approval.

## Note to the human

I, Routine A, can only draft. I did NOT create any tag, branch, or commit,
and I did not push. Please review this plan. If you approve:

    python loop-practice/loopprojects/loop11/gate.py approve

That prints a one-time approval token and the exact curl that fires
Routine B. The gate refuses to fire until you approve, and it only ever
creates the tag described on THIS page.
