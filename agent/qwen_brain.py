"""Core Qwen orchestration loop: recursive OpenAI-compatible tool-calling.

Connects to Qwen Cloud's OpenAI-compatible endpoint and lets qwen3.7-max
autonomously decide which shariah_engine-backed tools to call (agent/tools.py)
to answer the user's question. The only human-in-the-loop gate is on the
Rebalance Plan — see docs/adr/0001-read-only-advisor-boundary.md.
"""

import json
import logging
import os
from typing import Callable

from dotenv import load_dotenv
from openai import OpenAI

from agent.tools import TOOLS_SCHEMA, execute_tool

load_dotenv()

logger = logging.getLogger(__name__)

_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
_MODEL = "qwen3.7-max"
_MAX_TOOL_ROUNDS = 8

SYSTEM_PROMPT = """\
You are the Qwen Shariah Autopilot: an autonomous quantitative analyst for a \
Shariah-compliant equity Portfolio.

You have read-only tools to inspect the Eligible Universe, the current \
Portfolio, market regime, Factor Score ranking, sector concentration, \
holding volatility, live performance, and price history for outside \
benchmark tickers (e.g. GLDM, SOXQ — these are reference-only and never \
tradeable). You also have a `propose_rebalance` tool that computes a \
Rebalance Plan (sells/buys/target weights) — it NEVER submits any order.

If you call propose_rebalance, the resulting plan is shown to a human for \
approval before you see the final decision — incorporate their approved/ \
rejected verdict into your final report. Never claim that any trade was \
executed; you only ever report on proposed plans and their approval status.

When asked to analyze the Portfolio, produce a Risk & Performance Report \
covering: market regime, sector concentration, per-holding volatility, live \
Sharpe ratio / max drawdown / return, a Portfolio Narrative (plain-language \
interpretation of the above), and — if relevant — the Rebalance Plan and its \
HITL approval outcome.
"""


def _client() -> OpenAI:
    api_key = os.environ.get("QWEN_API_KEY")
    if not api_key:
        raise EnvironmentError("QWEN_API_KEY is not set")
    return OpenAI(base_url=_BASE_URL, api_key=api_key)


def run_conversation(
    user_message: str,
    history: list[dict] | None = None,
    hitl_gate: Callable[[dict], bool] | None = None,
) -> tuple[str, list[dict]]:
    """Run one user turn to completion, recursively resolving tool calls.

    Returns (final_assistant_text, updated_history). If given, `hitl_gate` is
    called synchronously with the proposed Rebalance Plan dict right after
    `propose_rebalance` executes; its bool return (approved/rejected) is
    injected into the tool result before Qwen sees it.
    """
    client = _client()
    messages = list(history) if history else [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": user_message})

    for _ in range(_MAX_TOOL_ROUNDS):
        response = client.chat.completions.create(
            model=_MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
        )
        choice = response.choices[0]
        messages.append(choice.message.model_dump(exclude_none=True))

        tool_calls = choice.message.tool_calls
        if not tool_calls:
            return choice.message.content or "", messages

        for call in tool_calls:
            name = call.function.name
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}

            logger.info("Qwen called tool: %s(%s)", name, arguments)
            result_json = execute_tool(name, arguments)

            if name == "propose_rebalance" and hitl_gate is not None:
                try:
                    plan = json.loads(result_json)
                except json.JSONDecodeError:
                    plan = {}
                if "error" not in plan:
                    approved = hitl_gate(plan)
                    plan["human_decision"] = "APPROVED" if approved else "REJECTED"
                    result_json = json.dumps(plan)

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": result_json,
            })

    # Ran out of tool-call rounds -- force a final answer without further tools.
    response = client.chat.completions.create(model=_MODEL, messages=messages)
    final = response.choices[0].message
    messages.append(final.model_dump(exclude_none=True))
    return final.content or "", messages
