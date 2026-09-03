# Cost of the dreaming loop — measured, not guessed

Each beat runs two fresh headless Claude agents (Dreamer + Checker) whose token usage is captured from each `claude -p` run JSON (see `runs/`). Numbers are **measured**, not modelled.

## Measured tokens per beat

| Beat | Date | Input | Output | Cache-read | Agent runs |
|------|------|-------|--------|------------|------------|

Totals over 0 beat(s): **0 input + 0 output tokens**; 0 agent runs.

Dollars = tokens × provider $/MTok / 1,000,000. The dominant term is the per-invocation harness overhead, not the loop's own content. This machine runs the loop's backend (`ANTHROPIC_MODEL=deepseek-v4-flash`), so substitute that provider's $/MTok for a real figure.
