# Roadmap: Path to Cloud-Native Scalability

This hackathon submission runs as a single-user interactive CLI against one Alpaca paper account. The path below outlines what changes as usage grows beyond a single terminal session.

## Phase 1 — Containerize and deploy (near-term)

- Package `agent/` + `shariah_engine/` into a Docker image; run on Alibaba Cloud ECS as a long-lived service (see `ALIBABA_DEPLOYMENT.md`).
- Move secrets (`ALPACA_API_KEY`, `QWEN_API_KEY`, etc.) out of `.env` files and into Alibaba Cloud KMS / instance-level environment injection.
- No architectural changes to `agent/tools.py` or `qwen_brain.py` — same read-only, single-account design, just no longer tied to one developer's laptop.

## Phase 2 — Cache the slow path, persist reports

- `get_factor_ranking` scores the full Eligible Universe live on every call (2-4 minutes). Add a caching layer (Alibaba Cloud Tair / Redis-compatible) so a Factor Score snapshot is computed on a schedule (e.g. hourly) rather than per-request, and tool calls read the cache.
- Persist Risk & Performance Reports and Rebalance Plan decisions to a real datastore (e.g. Alibaba Cloud RDS) instead of local markdown files, so report history survives restarts and is queryable.
- Add basic structured logging/metrics around tool-call latency and Qwen API usage.

## Phase 3 — Multi-user, multi-portfolio

- Generalize `shariah_engine.config.Config` (currently single Alpaca account, single ETF set) to support multiple portfolios/accounts per user.
- Move the tool-calling loop behind an API Gateway + async task queue, so long-running Factor Score computations don't block a single terminal session, and multiple users can query concurrently.
- The HITL Gate remains mandatory for any user's Rebalance Plan — scaling up does not relax the read-only-advisor boundary; it stays a deliberate, permanent constraint (see `docs/adr/0001-read-only-advisor-boundary.md`), not a stepping stone to autonomous execution.
