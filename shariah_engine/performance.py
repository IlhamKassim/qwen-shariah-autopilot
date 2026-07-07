"""Live performance metrics from a real Alpaca paper/live account's equity history.

Extracted from shariah-algo-trader's dashboard/api/routers/compare.py — same
Sharpe/drawdown/return math, stripped of the FastAPI/pydantic response models
and the unrelated second-account ("day trader") comparison feature.
"""

import datetime

import numpy as np

from shariah_engine.execution.alpaca_client import AlpacaClient

_RISK_FREE_RATE = 0.05  # annualised


def get_portfolio_history(client: AlpacaClient, period: str = "1M") -> tuple[list[str], list[float]]:
    """Return (dates, equity) for the account, most recent last."""
    data = client.get(f"/v2/account/portfolio/history?period={period}&timeframe=1D")
    timestamps: list[int] = data.get("timestamp", [])
    equities: list[float] = data.get("equity", [])

    dates = [
        datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime("%Y-%m-%d")
        for ts in timestamps
    ]
    paired = [(d, e) for d, e in zip(dates, equities) if e and e > 0]
    if not paired:
        return [], []
    dates_out, equities_out = zip(*paired)
    return list(dates_out), list(equities_out)


def compute_performance_metrics(equity: list[float]) -> dict:
    """Sharpe ratio, max drawdown, total return, and win rate from an equity curve."""
    if len(equity) < 2:
        return {
            "total_return_pct": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown_pct": 0.0,
            "current_equity": equity[-1] if equity else 0.0,
            "win_rate_pct": 0.0,
        }

    arr = np.array(equity, dtype=float)
    daily_returns = np.diff(arr) / arr[:-1]

    total_return = (arr[-1] / arr[0] - 1) * 100

    daily_rf = _RISK_FREE_RATE / 252
    excess = daily_returns - daily_rf
    sharpe = float((excess.mean() / excess.std()) * np.sqrt(252)) if excess.std() > 1e-8 else 0.0

    peaks = np.maximum.accumulate(arr)
    drawdowns = (arr - peaks) / peaks
    max_dd = float(drawdowns.min()) * 100

    win_days = int(np.sum(daily_returns > 0))
    win_rate = (win_days / len(daily_returns)) * 100

    return {
        "total_return_pct": round(total_return, 2),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "current_equity": round(float(arr[-1]), 2),
        "win_rate_pct": round(win_rate, 1),
    }
