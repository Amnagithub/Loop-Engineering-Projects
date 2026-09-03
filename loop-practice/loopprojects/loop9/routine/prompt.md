# Routine prompt — RECENT-COMMIT SUMMARY (GOOD version)

You are an automated one-shot routine. Work only inside this repository
(git root: `C:/Users/The-laptop-store/Documents/GitHub/Loop-Engineering-Projects`).
Do not touch files outside `loop-practice/loopprojects/loop9/routine/`.

## Goal
Publish a short markdown summary of the 5 most recent commits onto the
throwaway branch `claude/summary`.

## Steps
1. Read the input file `loop-practice/loopprojects/loop9/routine/context.md`.
   It lists 5 commit hashes, newest first.
   If that file is missing or unreadable, STOP immediately and report the
   error — do not improvise or substitute other input.
2. For each hash, get a one-line description:
   `git show -s --format='%h %ad %s' --date=short <hash>`
3. Write `loop-practice/loopprojects/loop9/routine/results/commit-summary.md`
   containing:
   - the run date,
   - one bullet per commit: hash, date, subject,
   - a 2–3 sentence takeaway describing what the batch of commits does.
4. Create branch `claude/summary` if it does not already exist, commit ONLY
   the new summary file to it (message: `routine: commit summary <YYYY-MM-DD>`),
   then switch back to the branch you started on. Do NOT push.
5. Print the exact relative path you wrote and the summary commit hash.

## Definition of done
The summary file exists on `claude/summary` and that branch's newest commit
contains exactly one file change (the summary).
