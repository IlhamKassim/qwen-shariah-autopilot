# Devpost Submission Draft

Copy the sections below into the Devpost project form. Fill in the bracketed placeholders before submitting.

---

## Project name

Qwen Shariah Autopilot

## Tagline (one line)

An autonomous quantitative analyst, built on Qwen3.7-Max, that reasons over a real Shariah-compliant trading account and gates every rebalance recommendation behind human approval.

## Track

**Track 4: Autopilot Agent**

## Links

- **Code repository:** https://github.com/IlhamKassim/qwen-shariah-autopilot (public, MIT licensed)
- **Demo video:** `[YouTube/Vimeo/Facebook link — add once recorded]`
- **Proof of Alibaba Cloud deployment recording:** `[add once recorded]`
- **Architecture diagram:** https://github.com/IlhamKassim/qwen-shariah-autopilot/blob/main/ARCHITECTURE.md
- **Alibaba Cloud API usage (code file):** https://github.com/IlhamKassim/qwen-shariah-autopilot/blob/main/agent/qwen_brain.py

## Detailed description

### The problem

Shariah-compliant equity investing operates under a hard compliance boundary: a stock is only tradeable while it sits inside a designated Shariah-certified ETF's current holdings. My pre-existing trading bot (`shariah-algo-trader`) already enforces this — it screens a universe, scores stocks on Momentum, Quality, Value, and Low-Volatility factors, and rebalances monthly. What it lacked was an autonomous reasoning layer: something that could interpret live performance, explain risk in plain language, and propose changes to a human — without ever being trusted to act unsupervised.

### What it does

Qwen Shariah Autopilot is a terminal agent, powered by **qwen3.7-max** via Qwen Cloud's OpenAI-compatible tool-calling API, that:

1. **Autonomously decides which of 9 read-only tools to call** in response to a natural-language question — fetching the Eligible Universe, scoring the current market regime, computing Factor Score rankings across Momentum/Quality/Value/Low-Volatility, reading live performance (Sharpe ratio, max drawdown, total return) from a real Alpaca paper-trading account, checking sector concentration against a compliance cap, and looking up external benchmark tickers (e.g. gold, semiconductors) for comparison commentary.
2. **Proposes a Rebalance Plan** — sells, buys, and inverse-volatility target weights — by replicating the production bot's own diff logic, including regime-gating (no new buys in a bear market), exactly as the real bot would compute it.
3. **Gates that plan behind a Human-in-the-Loop terminal approval step.** The orchestrator — not the model — enforces this: the human's approve/reject decision is injected into the tool result before Qwen's next turn, and the agent architecturally cannot submit an order. The order-submission module from the original engine was never even vendored into this repository.
4. **Writes a structured Risk & Performance Report** in markdown: market regime, live Sharpe/drawdown, sector concentration, per-holding volatility, the rebalance plan with its approval outcome, and a plain-language Portfolio Narrative.

### Technical Delta — what's pre-existing vs. built for this hackathon

**Pre-existing** (vendored unmodified into `shariah_engine/` from [`shariah-algo-trader`](https://github.com/IlhamKassim/shariah-algo-trader)): Factor Score computation, Eligible Universe / compliance-boundary fetching, market regime filter, and read-only Alpaca account access.

**Built from scratch for this hackathon** (`agent/`, `main.py`): the Qwen3.7-Max tool-calling orchestration loop, the 9-tool schema bridging Qwen to the engine, automated risk-report generation, the terminal HITL approval gate, and the read-only architectural boundary that makes autonomous operation safe to demo publicly. Full breakdown in the repo's README under "Technical Delta."

### Why this fits Track 4

The brief asks for agents that "automate real-world business workflows end-to-end," "handle ambiguous inputs," "invoke external tools," and "incorporate human-in-the-loop checkpoints at critical decision points" with an "emphasis on production-readiness over toy demos." This project: takes an open-ended natural-language question, autonomously chains multiple tool calls against live financial data and a real brokerage account, and places its one high-stakes decision — whether to act on a rebalance recommendation — behind a real human approval gate, with that boundary enforced at the code architecture level rather than by prompting alone.

### Built With

- Qwen Cloud (`qwen3.7-max`, OpenAI-compatible tool calling)
- Python, `openai` SDK, `pandas`, `numpy`, `pydantic`
- Alpaca (paper-trading account, read-only)
- `yfinance` (price and fundamentals data)
- Docker (containerized for Alibaba Cloud deployment — see `ALIBABA_DEPLOYMENT.md`)

---

## Notes for whoever fills this in

- Fill in the two `[...]` link placeholders once the video and Alibaba Cloud deployment proof are recorded.
- The "Built With" list should be updated if the Alibaba deployment path changes (e.g. add "Alibaba Cloud ECS" if real hosting ends up required).
