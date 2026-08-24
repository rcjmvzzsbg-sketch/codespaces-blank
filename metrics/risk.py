# metrics/risk.py
"""Risk & volatility metrics from price history: volatility, max drawdown,
Sharpe, Sortino, beta vs S&P 500, and trailing returns."""

import numpy as np
import pandas as pd
import yfinance as yf
from core.database import get_conn, write_facts
from config.universe import get_tickers

TRADING_DAYS = 252
_SPY_CACHE = {}


def _load_returns(ticker: str) -> pd.Series:
    conn = get_conn()
    df = conn.execute(
        "SELECT date, close FROM prices WHERE ticker=? ORDER BY date", [ticker]
    ).fetchdf()
    conn.close()
    if df.empty:
        return pd.Series(dtype=float)
    df = df.set_index("date")
    return df["close"].pct_change().dropna()


def _spy_returns() -> pd.Series:
    if "spy" in _SPY_CACHE:
        return _SPY_CACHE["spy"]
    try:
        spy = yf.download("SPY", period="5y", interval="1d",
                          progress=False, auto_adjust=True)
        if hasattr(spy.columns, "nlevels") and spy.columns.nlevels > 1:
            spy.columns = spy.columns.get_level_values(0)
        r = spy["Close"].pct_change().dropna()
        r.index = r.index.date
        _SPY_CACHE["spy"] = r
        return r
    except Exception as e:
        print(f"[risk] SPY fetch failed: {e}")
        return pd.Series(dtype=float)


def compute_risk(ticker: str, rf_annual: float = 0.04) -> list[dict]:
    rets = _load_returns(ticker)
    if len(rets) < 60:
        return []

    out = {}
    # Annualized volatility
    out["volatility_annual"] = float(rets.std() * np.sqrt(TRADING_DAYS) * 100)

    # Annualized return (geometric)
    total_ret = (1 + rets).prod()
    years = len(rets) / TRADING_DAYS
    ann_ret = total_ret ** (1 / years) - 1 if years > 0 else 0
    out["annual_return"] = float(ann_ret * 100)

    # Sharpe ratio (excess return / volatility)
    excess = ann_ret - rf_annual
    vol = rets.std() * np.sqrt(TRADING_DAYS)
    out["sharpe_ratio"] = float(excess / vol) if vol > 0 else None

    # Sortino ratio (downside deviation only)
    downside = rets[rets < 0]
    dd = downside.std() * np.sqrt(TRADING_DAYS)
    out["sortino_ratio"] = float(excess / dd) if dd > 0 else None

    # Max drawdown
    cum = (1 + rets).cumprod()
    running_max = cum.cummax()
    drawdown = (cum - running_max) / running_max
    out["max_drawdown"] = float(drawdown.min() * 100)

    # Trailing returns
    close = _load_returns(ticker)  # returns; rebuild price for windows
    conn = get_conn()
    px = conn.execute("SELECT close FROM prices WHERE ticker=? ORDER BY date", [ticker]).fetchdf()["close"]
    conn.close()
    if len(px) > TRADING_DAYS:
        out["return_1y"] = float((px.iloc[-1] / px.iloc[-TRADING_DAYS] - 1) * 100)
    if len(px) > 21:
        out["return_1m"] = float((px.iloc[-1] / px.iloc[-21] - 1) * 100)

    # Beta vs SPY
    spy = _spy_returns()
    if not spy.empty:
        aligned = pd.DataFrame({"stock": rets, "spy": spy}).dropna()
        if len(aligned) > 60:
            cov = aligned["stock"].cov(aligned["spy"])
            var = aligned["spy"].var()
            out["beta"] = float(cov / var) if var > 0 else None

    facts = []
    for metric, value in out.items():
        if value is not None and not (isinstance(value, float) and np.isnan(value)):
            facts.append({
                "ticker": ticker, "metric": metric, "period": "2026-08-24",
                "period_type": "point", "value": round(value, 3),
                "unit": "ratio", "source": "risk",
            })
    return facts


def compute_all() -> int:
    total = 0
    for ticker in get_tickers():
        facts = compute_risk(ticker)
        write_facts(facts)
        total += len(facts)
        print(f"  {ticker:<6} {len(facts):>3} risk metrics")
    print(f"\n✅ Risk metrics complete: {total} facts.")
    return total


if __name__ == "__main__":
    compute_all()
