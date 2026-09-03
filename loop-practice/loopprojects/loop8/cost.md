# Cost of the loop8 daily debt scan — measured, not guessed

Each beat runs fresh headless Claude agents (Maker + Checker), each a
real `claude -p` subprocess whose token usage is captured from the run
JSON (see `runs/`). Numbers below are **measured**, not modelled.

## Measured tokens per beat

| Beat | Date | Input | Output | Cache-read | Agent runs |
|------|------|-------|--------|------------|------------|
| 1 | 2026-09-03 | 65,163 | 19,840 | 391,552 | 2 |

Totals over 1 beat(s): **65,163 input + 19,840 output tokens**; mean ~65,163 input per beat.

## Monthly projection (once per day, 30 runs)

- Input: 65,163 × 30 ≈ **1,954,890 tokens/month**
- Output: 19,840 × 30 ≈ **595,200 tokens/month**

Dollars = `tokens × provider $/MTok / 1,000,000`. The dominant term is
the per-invocation harness overhead paid for every agent run, not the
loop's own content. Reference rates (illustrative only):

| Rate tier | Input $/MTok | Output $/MTok | ~Cost/month |
|-----------|--------------|---------------|-------------|
| Haiku 4.5-tier | $1.00 | $5.00 | ~$4.93 |
| Sonnet 5-tier | $2.00 | $10.00 | ~$9.86 |
| Opus 5-tier | $5.00 | $25.00 | ~$24.65 |

Two things to *not* trust: (1) `total_cost_usd` in the run JSON is a
guess — the harness reports it with `costBasis: unknown`; the token
counts are the reliable measurement. (2) This loop runs through this
machine's configured backend (`ANTHROPIC_MODEL=deepseek-v4-flash`), not Anthropic's first-party API — substitute the provider's $/MTok.
