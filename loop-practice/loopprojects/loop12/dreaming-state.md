# Dreaming state — Project 12 (The Dreaming Loop)

The single source of truth for the dreaming loop. `dream.py` reads the header
below to know where the last dream stopped, and rewrites it at the end of each
beat. **Rule changes never happen in this file** — they live on a
`claude/dream-<run>` branch awaiting a human merge; this file only records
that the branch was proposed.

## Header (machine-read; `- **key:** value` on the first lines)

- **state:** IDLE
- **run:** 0
- **last_dream:** 2026-09-02
- **branch:** —
- **proposal:** —

## What a dreaming beat is

A fresh engine reads the dated log entries and `progress.md` files the loops
left behind since `last_dream`, a deterministic scanner proves which
failure/correction signatures appear more than once, a **Dreamer** drafts the
smallest rule/skill improvement plus one deletion (both from the shared
`loopprojects/skills/` corpus), a **Checker** re-derives every citation, and
only on PASS the proposal is committed to a local `claude/dream-<run>` branch.
`last_dream` advances to today at the end of every completed beat.

## Dream ledger

| Run | Date | State | Branch | What was proposed |
|-----|------|-------|--------|-------------------|
