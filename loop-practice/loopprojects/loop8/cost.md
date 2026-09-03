# Cost of the loop8 daily debt scan — measured, not guessed

Each beat runs fresh headless Claude agents (Maker + Checker), each a
real `claude -p` subprocess whose token usage is captured from the run
JSON (see `runs/`). Numbers below are **measured**, not modelled.

## Measured tokens per beat

| Beat | Date | Input | Output | Cache-read | Agent runs |
|------|------|-------|--------|------------|------------|
| 1 | 2026-09-03 | 108,331 | 67,302 | 1,922,688 | 3 |

Totals over 1 beat(s): **108,331 input + 67,302 output tokens**; mean ~108,331 input per beat.

## Monthly projection (once per day, 30 runs)

- Input: 108,331 × 30 ≈ **3,249,930 tokens/month**
- Output: 67,302 × 30 ≈ **2,019,060 tokens/month**

Dollars = `tokens × provider $/MTok / 1,000,000`. The dominant term is
the per-invocation harness overhead paid for every agent run, not the
loop's own content. Reference rates (illustrative only):

| Rate tier | Input $/MTok | Output $/MTok | ~Cost/month |
|-----------|--------------|---------------|-------------|
| Haiku 4.5-tier | $1.00 | $5.00 | ~$0.30–0.60 |
| Sonnet 5-tier | $2.00 | $10.00 | ~$0.60–1.20 |
| Opus 5-tier | $5.00 | $25.00 | ~$1.50–3.00 |

Two things to *not* trust: (1) `total_cost_usd` in the run JSON is a
guess — the harness reports it with `costBasis: unknown`; the token
counts are the reliable measurement. (2) This loop runs through this
machine's configured backend (`ANTHROPIC_MODEL=deepseek-v4-flash`), not Anthropic's first-party API — substitute the provider's $/MTok.
