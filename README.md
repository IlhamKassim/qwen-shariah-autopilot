# Qwen Shariah Autopilot

An autonomous quantitative analyst, built on **Qwen3.7-Max**, that sits on top of a pre-existing Shariah-compliant equity trading engine. It reads live market data and a real Alpaca paper-trading account, autonomously decides which analyses to run via OpenAI-compatible function calling, and produces a structured Risk & Performance Report — gated by a human-in-the-loop approval step before any rebalance recommendation is finalized.

Built for the **Global AI Hackathon Series with Qwen Cloud — Track 4: Autopilot Agent**.

## Technical Delta

This repository combines two clearly separated layers. Judging this submission should focus on the second.

**Pre-existing (`shariah_engine/`, vendored unmodified from [`shariah-algo-trader`](https://github.com/IlhamKassim/shariah-algo-trader)):**
- Factor Score computation — Momentum, Quality, Value, Low-Volatility (`factors/`)
- Eligible Universe / Holdings Snapshot fetching, the Shariah-compliance boundary (`data/universe.py`)
- Market regime filter — SPY 200-day moving average (`data/regime.py`)
- Read-only Alpaca client and live Portfolio state reads (`execution/`)

**Built from scratch for this hackathon (`agent/`, `main.py`):**
- The autonomous Qwen3.7-Max orchestration loop with recursive OpenAI-compatible tool calling (`agent/qwen_brain.py`)
- A 9-tool schema wrapping the engine as callable tools (`agent/tools.py`), including new logic for sector-concentration reporting, external benchmark price lookups, and Rebalance Plan computation
- Automated Risk & Performance Report generation: regime + sector concentration + per-holding volatility + live Sharpe/drawdown, plus an LLM-generated Portfolio Narrative
- A Human-in-the-Loop safety gate enforced at the orchestrator level (never delegated to the model) with a strict read-only boundary — the agent computes and proposes but never submits an order
- The interactive terminal client (`main.py`)

See `agent/CONTEXT.md` for the full glossary of what these new concepts mean, and `docs/adr/0001-read-only-advisor-boundary.md` for why the agent never executes trades.

## Architecture

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full diagram (Qwen Cloud ↔ agent ↔ Shariah Engine ↔ Alpaca/yfinance). Summary:

```
shariah_engine/     read-only vendored engine (Factor Score math, universe/compliance, live reads)
agent/
  tools.py          TOOLS_SCHEMA + execute_tool() dispatcher bridging Qwen to shariah_engine
  qwen_brain.py      recursive tool-calling loop against Qwen Cloud + the HITL gate hook
main.py              interactive terminal client, HITL approval prompt, report writer
```

The agent never calls `OrderExecutor` — that module was deliberately not vendored at all. A `propose_rebalance` tool computes what a rebalance *would* look like (sells/buys/target weights, regime-gated exactly like the production bot), a human approves or rejects it in the terminal, and the verdict is folded into the final report. Executing an approved plan is a manual step via the existing `shariah-algo-trader` bot/dashboard.

## Setup

**Prerequisites:** Python 3.11+, an Alpaca paper-trading account, a Qwen Cloud API key.

```bash
git clone <this-repo-url>
cd qwen-shariah-autopilot

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Fill in ALPACA_API_KEY, ALPACA_API_SECRET, ALPACA_BASE_URL, ETF_SYMBOL, TOP_N, QWEN_API_KEY
```

## Running

```bash
python main.py
```

Example prompts:
- `Analyze the portfolio and tell me if we should rebalance`
- `What's our current risk exposure and how does it compare to gold (GLDM) this year?`

Each turn's final answer is saved to `reports/report_<timestamp>.md`.

## Environment variables

See `.env.example`. All Alpaca/ETF/Qwen configuration is read from environment variables; no secrets are committed.
