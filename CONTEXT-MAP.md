# Context Map

## Contexts

- [Shariah Engine](./shariah_engine/CONTEXT.md) — the vendored, read-only Shariah-compliant trading engine (factor scoring, universe/compliance, live execution). Copied from `shariah-algo-trader`; do not edit its language or its code.
- [Autopilot Agent](./agent/CONTEXT.md) — the new Qwen-driven orchestration layer built for this hackathon: tool-calling, analysis reporting, and the human-in-the-loop approval gate.

## Relationships

- **Autopilot Agent → Shariah Engine**: the Agent calls the Engine's read-only functions (universe fetch, factor scoring, live Alpaca position/performance reads) as tools. It never calls the Engine's order-submission functions (`OrderExecutor`) — see [[read-only-advisor]] in the Autopilot Agent context.
