"""Interactive terminal client for the Qwen Shariah Autopilot.

Run: python main.py
"""

import datetime
from pathlib import Path

from agent.qwen_brain import run_conversation

REPORTS_DIR = Path("reports")


def _print_plan(plan: dict) -> None:
    print("\n" + "=" * 60)
    print("PROPOSED REBALANCE PLAN (no orders will be submitted)")
    print("=" * 60)
    print(f"Regime: {plan.get('regime')}")
    if plan.get("note"):
        print(f"Note: {plan['note']}")
    print(f"Sells: {plan.get('sells') or '(none)'}")
    print(f"Buys:  {plan.get('buys') or '(none)'}")
    print(f"Stays: {plan.get('stays') or '(none)'}")
    print("Target weights:")
    for ticker, weight in (plan.get("target_weights") or {}).items():
        print(f"  {ticker}: {weight:.2%}")
    print("=" * 60)


def hitl_gate(plan: dict) -> bool:
    """Terminal HITL Gate: show the Rebalance Plan and require explicit approval.

    Approval only stamps the plan APPROVED in the conversation/report -- it
    never submits an order. See docs/adr/0001-read-only-advisor-boundary.md.
    """
    _print_plan(plan)
    while True:
        answer = input("Approve this Rebalance Plan? [y/N]: ").strip().lower()
        if answer in ("y", "yes"):
            print("APPROVED -- no orders submitted; execute manually if desired.\n")
            return True
        if answer in ("", "n", "no"):
            print("REJECTED.\n")
            return False
        print("Please answer y or n.")


def _save_report(text: str) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"report_{timestamp}.md"
    path.write_text(text)
    return path


def main() -> None:
    print("Qwen Shariah Autopilot -- type a question, or 'exit' to quit.")
    print('(e.g. "Analyze the portfolio and tell me if we should rebalance")\n')

    history: list[dict] | None = None

    while True:
        try:
            user_message = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_message:
            continue
        if user_message.lower() in ("exit", "quit"):
            break

        print("\n(thinking -- this may take a few minutes if a full universe scan is needed)\n")
        answer, history = run_conversation(user_message, history=history, hitl_gate=hitl_gate)

        print(answer)
        path = _save_report(answer)
        print(f"\n[report saved to {path}]\n")


if __name__ == "__main__":
    main()
