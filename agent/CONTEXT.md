# Autopilot Agent

The Qwen-driven orchestration layer built for the hackathon. It calls into the read-only [Shariah Engine](../shariah_engine/CONTEXT.md) via tool use, produces analysis reports, and gates any rebalancing recommendation behind human approval. It never places orders itself.

## Language

**Live Snapshot Analysis**:
The agent's core analysis action: compute today's Factor Score ranking from the Eligible Universe (via the Engine's factor functions, which always score the current day — no historical date parameter exists) and pull real Sharpe ratio / max drawdown / total return from the live Alpaca paper account's equity history. Replaces the originally-pitched "historical backtest," which does not exist in the Engine and was not built new to preserve the black-box constraint.
_Avoid_: backtest, simulation, historical analysis

**Rebalance Plan**:
A proposed set of sells/buys/target-weight adjustments computed by the Agent using only the Engine's read-only functions (universe fetch, factor scoring, current Alpaca positions) — never the Engine's `OrderExecutor`. Distinct from the Engine's own Rebalance, which reads live state AND submits orders in one step. A Rebalance Plan is inert until a human reviews it.
_Avoid_: rebalance instructions, trade recommendation, order plan

**Benchmark Reference**:
Raw price history for a ticker outside the Eligible Universe (e.g. GLDM, SOXQ), fetched solely so the Portfolio Narrative can compare the Shariah Portfolio's performance against it. Never feeds into Factor Score, the Rebalance Plan, or any trade decision — the Eligible Universe boundary is untouched. Distinct from the Eligible Universe itself, which is the only tradeable set.
_Avoid_: comparison ticker, external ticker, reference asset

**Portfolio Narrative**:
Qwen's natural-language interpretation of a Live Snapshot Analysis — a written analyst take on positioning, regime, and concentration, generated from existing Engine outputs. Not a distinct signal or data source; no news/social sentiment is ingested. Replaces the originally-pitched "sentiment analysis," which would have required a new data pipeline outside the Engine's scope.
_Avoid_: sentiment analysis, sentiment score, news sentiment

**HITL Gate**:
The terminal confirmation step where a human reviews a Rebalance Plan and either approves or rejects it. Approval only stamps the plan as APPROVED in the session report — it never triggers order submission. Read-only advisor is a deliberate scope decision: see [[read-only-advisor]].
_Avoid_: approval flow, confirmation prompt, safety check

**Risk & Performance Report**:
The structured markdown document the Agent produces each session, combining: regime status (bull/bear via SPY 200-day MA), sector concentration (GICS weights vs. the 20% cap), per-holding annualised volatility, live Sharpe ratio / max drawdown from the real paper account, the Portfolio Narrative, and — if one was proposed — the Rebalance Plan and its HITL Gate outcome. This is the single top-level artifact tying every other concept together.
_Avoid_: performance report, summary, output

## Example Dialogue

> **Dev**: The agent said "approved" after I confirmed the rebalance — did it just sell my AAPL position?
>
> **Domain expert**: No. Approval only stamps the Rebalance Plan as APPROVED in the report. The Agent never calls the Engine's OrderExecutor — that boundary is intentional so an LLM mistake can never touch a real account. If you want the trades placed, you execute them yourself through the existing bot or dashboard.
>
> **Dev**: So what's the point of the HITL Gate if nothing gets executed?
>
> **Domain expert**: It's still gating a real decision — the Agent is autonomously deciding *what* the ideal Portfolio should look like and presenting it as a recommendation. The human is the one who decides whether that recommendation is acted on at all, which is the actual high-stakes step.
