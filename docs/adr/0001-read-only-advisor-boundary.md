# Agent never places orders — HITL approval only stamps a Rebalance Plan

The Autopilot Agent could either submit real (paper) orders through the Engine's `OrderExecutor` after HITL approval, or stop at producing an approved Rebalance Plan for a human to execute manually. We chose the latter: the agent computes plans using only the Engine's read-only functions and never calls order-submission code, so an LLM tool-calling mistake can never touch a live or paper account. This was a deliberate safety/scope trade-off for a public hackathon demo over the more "autonomous-looking" alternative of wiring real execution behind the approval gate.

## Considered Options

- Real paper-trade execution: agent calls `OrderExecutor` after approval. Rejected — requires new orchestration code to split the Engine's fused diff+execute `run_rebalance`, and risks an agentic mistake placing real orders during a live demo.
- Read-only advisor (chosen): agent stops at an approved plan; a human executes elsewhere via the existing bot/dashboard.
