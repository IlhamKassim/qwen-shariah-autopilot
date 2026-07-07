# Demo Video Script (~3 minutes)

Target: Devpost submission video for **Track 4: Autopilot Agent**. Upload publicly to YouTube/Vimeo/Facebook Video.

## Before recording

- Have `python main.py` ready in a terminal with a real `.env` (Alpaca + `QWEN_API_KEY` already confirmed working).
- The first `get_factor_ranking` tool call takes several minutes (full SPUS+HLAL universe scan via yfinance). **Don't record that wait live.** Either:
  - Pre-run the session once, capture the terminal output/report, and re-enact narrating over a sped-up screen capture (2-4x timelapse on the scoring portion only), or
  - Cut from "Qwen just called `get_factor_ranking`..." straight to the completed ranking with a jump cut / "here's what came back" transition.
- Have `reports/report_20260707_141707.md` (or a fresh run's report) open in a second window as backup b-roll in case live narration needs a steady reference.

## Script

**[0:00–0:15] Hook — the problem**

> "Shariah-compliant investing means every trade has to respect a hard compliance boundary — you can only ever hold what's currently inside a Shariah-certified ETF's holdings. My existing trading bot already enforces that. What it didn't have was an autonomous layer that could reason about performance, explain risk in plain language, and propose changes — safely. That's what I built for Track 4: Autopilot Agent."

**[0:15–0:45] Architecture walkthrough** — *show `ARCHITECTURE.md`'s diagram on screen*

> "Here's the shape of it. Qwen Cloud — specifically qwen3.7-max — sits at the center as the reasoning engine, connected through an OpenAI-compatible tool-calling loop. It has nine read-only tools it can call autonomously: fetching the Eligible Universe, scoring stocks on Momentum, Quality, Value, and Low-Volatility factors, checking market regime, pulling live performance from a real Alpaca paper-trading account, and — critically — proposing a rebalance plan. Everything below the agent layer is a pre-existing Shariah trading engine I built before this hackathon; I vendored it in as a read-only black box and never touched its math."

**[0:45–1:05] Technical Delta** — *show README's Technical Delta section*

> "To be explicit about what's new: the Factor Score math, the compliance-universe fetching, and the live Alpaca reads all pre-date this hackathon. What's new is everything in this diagram in blue — the Qwen orchestration loop, the tool schema bridging Qwen to that engine, the automated risk reporting, and the human-in-the-loop safety gate."

**[1:05–2:30] Live demo**

> "Let's run it." *(type and run `python main.py`)*
>
> "I'll ask: 'Analyze the portfolio and tell me if we should rebalance.'" *(enter prompt — cut/timelapse through the tool-calling wait)*
>
> "Qwen is autonomously deciding which tools to call — market regime, sector concentration, live performance, and here —" *(show terminal)* "— it's called `propose_rebalance`. This is the safety boundary: the agent computed a full sell/buy/target-weight plan, but it stops here and waits for me."
>
> *(show the printed plan + `Approve this Rebalance Plan? [y/N]:` prompt)*
>
> "I approve it —" *(type `y`)* "— and notice what prints: 'APPROVED — no orders submitted; execute manually if desired.' The agent never calls the broker's order-submission API. It only proposes."
>
> *(scroll through the generated Risk & Performance Report)*
>
> "And here's the full report Qwen wrote: market regime, live Sharpe ratio and drawdown from the real paper account, sector concentration against the compliance cap, per-holding volatility, the rebalance plan with reasoning per ticker, and a plain-language narrative tying it together."

**[2:30–2:50] Why this matters for Track 4**

> "This is exactly the shape the track asks for: ambiguous natural-language input, autonomous multi-tool orchestration, and a human-in-the-loop checkpoint at the one decision that actually matters — whether to act on the recommendation. And it's read-only by design: see the ADR in the repo — the agent architecturally cannot submit a trade, by omission, not by a runtime check."

**[2:50–3:00] Close**

> "Full code, architecture diagram, and docs are in the repo linked below. Thanks for watching."

## On-screen elements checklist

- [ ] `ARCHITECTURE.md` diagram (rendered, e.g. via GitHub's markdown preview)
- [ ] README's Technical Delta section
- [ ] Live (or lightly edited) terminal run of `main.py`
- [ ] The HITL approval prompt and its "APPROVED — no orders submitted" output, clearly visible
- [ ] The final generated Risk & Performance Report, scrolled through
- [ ] Repo URL visible at the end (README/About section showing the public MIT license badge)
