# Architecture

This is a terminal-based agent — there is no database or web frontend. The diagram below shows every component in the actual request path: how Qwen Cloud connects to the orchestration layer, the read-only Shariah Engine, and the external data sources (Alpaca, yfinance, ETF holdings feeds).

```mermaid
flowchart TD
    Human(["Human (terminal)"])

    subgraph NEW["agent/ + main.py — built for this hackathon"]
        Main["main.py<br/>REPL + HITL Gate"]
        Brain["agent/qwen_brain.py<br/>run_conversation()<br/>recursive tool-calling loop"]
        Tools["agent/tools.py<br/>TOOLS_SCHEMA + execute_tool()"]
    end

    Qwen[["Qwen Cloud<br/>qwen3.7-max<br/>(Alibaba Cloud — OpenAI-compatible API)"]]

    subgraph ENGINE["shariah_engine/ — vendored, read-only black box"]
        Factors["factors/<br/>Momentum · Quality · Value · Volatility · Scorer"]
        Data["data/<br/>universe.py (Eligible Universe)<br/>regime.py (bull/bear)"]
        Exec["execution/<br/>alpaca_client.py · portfolio.py<br/>(reads only — no order submission)"]
        Perf["performance.py<br/>Sharpe / drawdown / return"]
    end

    subgraph EXTERNAL["External services"]
        Alpaca[("Alpaca API<br/>paper-trading account")]
        YFinance[("yfinance<br/>prices + fundamentals")]
        ETFFeeds[("SPUS / HLAL<br/>holdings CSV feeds")]
    end

    Reports[("reports/*.md<br/>saved session output")]

    Human -- "question" --> Main
    Main -- "run_conversation()" --> Brain
    Brain <-->|"chat.completions.create() / tool_calls"| Qwen
    Brain -- "execute_tool(name, args)" --> Tools

    Tools --> Factors
    Tools --> Data
    Tools --> Exec
    Tools --> Perf

    Exec --> Alpaca
    Factors --> YFinance
    Data --> ETFFeeds

    Tools -. "propose_rebalance result" .-> Brain
    Brain -. "plan dict" .-> Main
    Main -- "Approve? [y/N]" --> Human
    Human -- "decision" --> Main
    Main -. "human_decision injected<br/>into tool result" .-> Brain

    Brain -- "final report" --> Main
    Main --> Reports

    style NEW fill:#e8f4fd,stroke:#2b6cb0
    style ENGINE fill:#fdf6e3,stroke:#b7791f
    style EXTERNAL fill:#f0f0f0,stroke:#718096
    style Qwen fill:#fde8e8,stroke:#c53030
```

## Key boundaries

- **The agent never calls `OrderExecutor`.** `shariah_engine/execution/` only contains read functions (`alpaca_client.get`, `portfolio.get_current_portfolio`). The order-submission module from the original engine was deliberately never vendored — see [`docs/adr/0001-read-only-advisor-boundary.md`](docs/adr/0001-read-only-advisor-boundary.md).
- **The HITL Gate lives in `main.py`, not inside the model.** Qwen never decides whether a Rebalance Plan is approved — the terminal blocks on real human input, and the decision is injected into the tool result before Qwen's next turn.
- **Qwen Cloud is the only Alibaba Cloud service in the request path** — `agent/qwen_brain.py` calls `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` (Qwen Cloud's OpenAI-compatible endpoint) for every reasoning/tool-calling step.
