# Cost of the Loop 7 morning-brief — measured, not guessed

Each beat is a real headless Claude Code run (`claude -p`, the deployment shape
of a scheduled daily loop). Usage was captured from each run's JSON result
(see `runs/beat-*.json`). All numbers below are **measured**, not modelled.

## Measured tokens per beat (this project's 4 runs)

| Beat | Date | Input | Output | cache_read* | Result |
|------|-----------|-------|--------|-------------|--------|
| 1 | 2026-09-04 | 18,640 | 1,698 | 108,928 | FAILED (recorded) |
| 2 | 2026-09-05 | 20,008 | 2,306 | 71,296 | FAILED (recorded) |
| 3 | 2026-09-06 | 25,713 | 7,971 | 159,744 | ESCALATED (wrote the Needs Human note) |
| 4 | 2026-09-07 | 19,750 | 1,439 | 54,656 | HOLD (did nothing but check State) |
| **Total** | | **84,111** | **13,414** | | |

\* `cache_read_input_tokens` as reported by the backend. Not relied on here —
see *Cache caveats* below.

## Where the tokens go: fixed overhead dominates

A bare invocation that does *nothing* ("reply NESTED_OK", no project files) cost
**18,482 input tokens** — the Claude Code harness + tool schema loaded on every
run. Content is nearly free next to that:

- Beat 1 (reads skill + spine + log, one failed read, edits 2 files): input
  was only **~160 tokens above the bare overhead**.
- Beat 3 spent more input (25,713) because the spine had grown and it wrote the
  structured Needs Human note (output 7,971).
- Beat 4 **did nothing** (a HOLD) and still cost **19,750 input tokens**.

**Planning number for a healthy daily run ≈ 20,000 input + ~2,000 output
tokens** (beats 1–2 are the normal mechanics; a SUCCESS beat is the same plus
copying a one-line brief — a ~50-token difference).

## Monthly cost, once per day (30 runs)

- Input: 20,000 × 30 = **600,000 tokens/month**
- Output: 2,000 × 30 = **60,000 tokens/month**
- Total ≈ **660,000 tokens/month**

Dollars = `600,000 × in_rate + 60,000 × out_rate`, divided by 1,000,000.
Reference figures at Anthropic first-party list rates (illustrative only — see
*Which rate applies?*):

| Rate tier | Input $/MTok | Output $/MTok | Cost/month | Cost/year |
|-----------|--------------|---------------|------------|-----------|
| Haiku 4.5-tier | $1.00 | $5.00 | **~$0.90** | ~$11 |
| Sonnet 5-tier | $2.00 | $10.00 | **~$1.80** | ~$22 |
| Opus 5-tier | $5.00 | $25.00 | **~$4.50** | ~$54 |
| **Your actual rate** | _provider's_ | _provider's_ | _= 0.6×in + 0.06×out_ | — |

So a once-daily agentic morning brief is roughly **a few dollars a month** — the
dominant term is the **~18.5k-token harness overhead paid every single run**,
not the loop's own content.

## Which rate applies here

This loop runs through this machine's configured backend
(`ANTHROPIC_BASE_URL`, `ANTHROPIC_MODEL=deepseek-v4-flash`), not Anthropic's
first-party API. The **real bill is whatever that provider charges per token** —
substitute its $/MTok in the formula above. Two things to *not* trust:

1. **`total_cost_usd` in the run JSON is a guess.** The harness reports it with
   `costBasis: "unknown"` and the implied input-only rate swings between
   **$8.2 and $15.9/MTok across these four otherwise-identical runs** — it is a
   default price table applied to an unknown model, not an invoice. The token
   counts are the reliable measurement; the dollar figure is not.
2. **`cache_read` numbers are backend-reported and large** (55k–160k per run,
   i.e. the harness prompt re-read across the run's tool turns). If the provider
   discounts cached reads the true cost is *lower* — but a **once-daily cadence
   spans far beyond any prompt-cache TTL**, so there is no cross-run caching to
   rely on: each morning pays full input price.

## The observability×cost finding

Beat 4 (HOLD) did zero work and still cost ~19,750 input tokens. A loop that
**escalates but keeps being scheduled** burns the full daily overhead forever
doing nothing. The fix is not just "escalate" — it is *stop the scheduler when
`State: NEEDS_HUMAN`* (or make the scheduler itself read the State flag before
waking a beat). Observability and cost are the same design problem here.

## What this project itself cost (disclosure)

4 beats + 1 smoke test ≈ **103k input + 13k output tokens** (~0.12 MTok) — on
the order of $0.10–$0.60 at the reference rates above, run to learn the lesson.
