"""OpenAI-format tool schema and dispatcher exposing shariah_engine to Qwen.

Read-only bridge: every tool here either reads live data (Alpaca positions/
performance, yfinance prices) or computes a proposed Rebalance Plan. Nothing
in this module ever submits an order — shariah_engine's OrderExecutor and
jobs/ (which do submit orders) were deliberately not vendored at all. See
docs/adr/0001-read-only-advisor-boundary.md.
"""

import datetime
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

import numpy as np
import yfinance as yf

from shariah_engine.config import Config
from shariah_engine.data.regime import is_bull_market
from shariah_engine.data.universe import UniverseError, fetch_combined_universe
from shariah_engine.execution.alpaca_client import AlpacaClient, AlpacaError
from shariah_engine.execution.portfolio import get_current_portfolio as _read_current_portfolio
from shariah_engine.factors.momentum import compute_momentum_factor
from shariah_engine.factors.quality import compute_quality_factor
from shariah_engine.factors.scorer import rank_by_factor_score
from shariah_engine.factors.value import compute_value_factor
from shariah_engine.factors.volatility import (
    compute_inv_vol_weights,
    compute_raw_volatility,
    compute_volatility_factor,
)
from shariah_engine.performance import compute_performance_metrics, get_portfolio_history

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _config() -> Config:
    return Config()


@lru_cache(maxsize=1)
def _alpaca_client() -> AlpacaClient:
    cfg = _config()
    return AlpacaClient(cfg.alpaca_api_key, cfg.alpaca_api_secret, cfg.alpaca_base_url)


def _json_default(obj):
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, (set, frozenset)):
        return sorted(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def get_eligible_universe() -> dict:
    cfg = _config()
    universe = fetch_combined_universe(cfg.etf_symbols)
    return {"etf_symbols": cfg.etf_symbols, "universe_size": len(universe), "tickers": sorted(universe)}


def get_current_portfolio() -> dict:
    portfolio = _read_current_portfolio(_alpaca_client())
    return {"holdings": sorted(portfolio), "count": len(portfolio)}


def get_regime_status() -> dict:
    bull = is_bull_market()
    return {"regime": "bull" if bull else "bear", "new_buys_allowed": bull}


def get_factor_ranking(top_n: int | None = None) -> dict:
    cfg = _config()
    top_n = top_n or cfg.top_n
    universe = fetch_combined_universe(cfg.etf_symbols)

    momentum = compute_momentum_factor(universe)
    quality = compute_quality_factor(universe)
    raw_vols = compute_raw_volatility(universe)
    volatility = compute_volatility_factor(raw_vols)
    value = compute_value_factor(universe)

    ranked = rank_by_factor_score(momentum, quality, volatility, value, top_n, cfg.sector_cap)

    breakdown = []
    for ticker in ranked:
        m, q = momentum.get(ticker, 0.0), quality.get(ticker, 0.0)
        v, val = volatility.get(ticker, 0.0), value.get(ticker, 0.0)
        breakdown.append({
            "ticker": ticker,
            "momentum_z": round(m, 3),
            "quality_z": round(q, 3),
            "low_vol_z": round(v, 3),
            "value_z": round(val, 3),
            "factor_score": round(0.25 * m + 0.25 * q + 0.25 * v + 0.25 * val, 3),
        })

    return {"top_n": top_n, "sector_cap": cfg.sector_cap, "ranking": breakdown}


def _fetch_one_sector(ticker: str) -> tuple[str, str]:
    try:
        info = yf.Ticker(ticker).info
        return ticker, info.get("sector", "Unknown") or "Unknown"
    except Exception:
        return ticker, "Unknown"


def _fetch_sectors(tickers: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(_fetch_one_sector, t): t for t in tickers}
        for future in as_completed(futures):
            ticker, sector = future.result()
            result[ticker] = sector
    return result


def get_sector_concentration(tickers: list[str] | None = None) -> dict:
    cfg = _config()
    if not tickers:
        tickers = sorted(_read_current_portfolio(_alpaca_client()))

    sectors = _fetch_sectors(tickers)
    counts: dict[str, int] = {}
    for t in tickers:
        s = sectors.get(t, "Unknown")
        counts[s] = counts.get(s, 0) + 1

    n = len(tickers) or 1
    weights = {s: round(c / n, 3) for s, c in counts.items()}
    max_per_sector = max(1, int(cfg.sector_cap * n))

    return {
        "holdings_by_sector": counts,
        "sector_weights": weights,
        "sector_cap_pct": cfg.sector_cap,
        "max_holdings_per_sector": max_per_sector,
        "over_cap": [s for s, c in counts.items() if c > max_per_sector],
    }


def get_holding_volatility(tickers: list[str] | None = None) -> dict:
    if not tickers:
        tickers = sorted(_read_current_portfolio(_alpaca_client()))
    raw_vols = compute_raw_volatility(set(tickers))
    ranked = sorted(raw_vols.items(), key=lambda kv: -kv[1])
    return {"volatility_by_ticker": {t: round(v, 4) for t, v in ranked}}


def get_live_performance(period: str = "1M") -> dict:
    _dates, equity = get_portfolio_history(_alpaca_client(), period=period)
    metrics = compute_performance_metrics(equity)
    return {"period": period, "data_points": len(equity), **metrics}


def get_price_history(ticker: str, lookback_days: int = 365) -> dict:
    end = datetime.date.today()
    start = end - datetime.timedelta(days=lookback_days)
    data = yf.download(ticker, start=str(start), end=str(end), auto_adjust=True, progress=False)
    if data.empty:
        return {"ticker": ticker, "error": "no price data returned"}

    close = data["Close"]
    if hasattr(close, "squeeze"):
        close = close.squeeze()
    series = close.dropna()
    first, last = float(series.iloc[0]), float(series.iloc[-1])

    return {
        "ticker": ticker,
        "start_date": str(series.index[0].date()),
        "end_date": str(series.index[-1].date()),
        "start_price": round(first, 2),
        "end_price": round(last, 2),
        "period_return_pct": round((last / first - 1) * 100, 2) if first else 0.0,
    }


def propose_rebalance() -> dict:
    """Compute a Rebalance Plan without submitting any order.

    Mirrors the production bot's own Rebalance diff (sells/stays/buys, inv-vol
    target weights, regime-gated buys) using only read-only Engine functions,
    so the plan matches what the real bot would do if a human executed it.
    """
    cfg = _config()
    current = _read_current_portfolio(_alpaca_client())
    universe = fetch_combined_universe(cfg.etf_symbols)

    ranking = get_factor_ranking(cfg.top_n)
    target = [row["ticker"] for row in ranking["ranking"]]
    eligible_target = {t for t in target if t in universe}

    raw_vols = compute_raw_volatility(eligible_target)
    target_weights = compute_inv_vol_weights(sorted(eligible_target), raw_vols)

    regime = get_regime_status()

    sells = sorted(current - eligible_target)
    stays = sorted(current & eligible_target)
    buys = sorted(eligible_target - current) if regime["new_buys_allowed"] else []

    note = None
    if not regime["new_buys_allowed"]:
        note = (
            "Regime is bearish (SPY below 200-day MA) — the production bot skips "
            "all new buys in this state, so this plan proposes no buys."
        )

    return {
        "sells": sells,
        "stays": stays,
        "buys": buys,
        "target_weights": {t: round(w, 4) for t, w in target_weights.items()},
        "regime": regime["regime"],
        "note": note,
    }


# ---------------------------------------------------------------------------
# OpenAI-format tool schema
# ---------------------------------------------------------------------------

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_eligible_universe",
            "description": (
                "Return the current Shariah-compliant Eligible Universe: individual stocks "
                "currently held by the configured Shariah ETFs (e.g. SPUS/HLAL). This is the "
                "only set of tickers that may ever appear in the Portfolio or a Rebalance Plan."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_portfolio",
            "description": "Return the current Portfolio holdings, read live from the Alpaca paper-trading account.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_regime_status",
            "description": (
                "Return the current market regime (bull/bear) based on whether SPY is above or "
                "below its 200-day moving average. In a bear regime, the production bot skips all new buys."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_factor_ranking",
            "description": (
                "Run a Live Snapshot Analysis: score every stock in the Eligible Universe on "
                "Momentum, Quality, Value, and Low-Volatility factors, and return the top-N ranked "
                "by composite Factor Score. This is the slowest tool (several minutes) since it "
                "fetches live price and fundamentals data for the full universe via yfinance."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "top_n": {
                        "type": "integer",
                        "description": "Number of top-ranked stocks to return. Defaults to the configured TOP_N.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sector_concentration",
            "description": (
                "Return GICS sector weights for a list of tickers (defaults to the current "
                "Portfolio) and whether any sector exceeds the configured concentration cap."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tickers to analyze. Defaults to the current Portfolio holdings if omitted.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_holding_volatility",
            "description": (
                "Return annualised price volatility for a list of tickers (defaults to the "
                "current Portfolio), ranked from most to least volatile."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tickers to analyze. Defaults to the current Portfolio holdings if omitted.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_live_performance",
            "description": (
                "Return Sharpe ratio, max drawdown, total return, and win rate computed from the "
                "real Alpaca paper-trading account's actual equity history. This is real live "
                "performance, not a simulated backtest."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Alpaca portfolio history period, e.g. '1M', '3M', '1A'. Defaults to '1M'.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_price_history",
            "description": (
                "Fetch raw price history for ANY ticker (e.g. GLDM, SOXQ) purely as a Benchmark "
                "Reference for comparison commentary. This ticker is NOT part of the Shariah "
                "Eligible Universe and can never be traded or included in a Rebalance Plan."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Ticker symbol to fetch, e.g. GLDM or SOXQ."},
                    "lookback_days": {
                        "type": "integer",
                        "description": "Number of calendar days of history to fetch. Defaults to 365.",
                    },
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_rebalance",
            "description": (
                "Compute a Rebalance Plan: the sells/buys/target-weight adjustments that would "
                "bring the Portfolio in line with the current top-N Factor Score ranking. This "
                "NEVER submits any order — it only returns a proposed plan for human review via "
                "the HITL Gate."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


_DISPATCH = {
    "get_eligible_universe": lambda args: get_eligible_universe(),
    "get_current_portfolio": lambda args: get_current_portfolio(),
    "get_regime_status": lambda args: get_regime_status(),
    "get_factor_ranking": lambda args: get_factor_ranking(args.get("top_n")),
    "get_sector_concentration": lambda args: get_sector_concentration(args.get("tickers")),
    "get_holding_volatility": lambda args: get_holding_volatility(args.get("tickers")),
    "get_live_performance": lambda args: get_live_performance(args.get("period", "1M")),
    "get_price_history": lambda args: get_price_history(args["ticker"], args.get("lookback_days", 365)),
    "propose_rebalance": lambda args: propose_rebalance(),
}


def execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute a tool by name and return a JSON string result. Never raises.

    Errors are caught and returned as {"error": ...} so the Qwen tool-calling
    loop can incorporate the failure into its next turn instead of crashing.
    """
    handler = _DISPATCH.get(tool_name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    try:
        result = handler(arguments or {})
    except (UniverseError, AlpacaError) as exc:
        logger.warning("%s failed: %s", tool_name, exc)
        return json.dumps({"error": str(exc)})
    except Exception as exc:
        logger.exception("%s raised an unexpected error", tool_name)
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"})

    return json.dumps(result, default=_json_default)
