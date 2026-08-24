# metrics/growth2.py
"""Multi-horizon growth: 1yr, 3yr, 5yr CAGR across key line items.
Reveals trajectory (accelerating vs decelerating), not just a snapshot."""

from core.database import get_conn, write_facts
from config.universe import get_tickers

# Line items to compute multi-window growth for
ITEMS = [
    "revenue", "net_income", "operating_income", "gross_profit",
    "free_cash_flow", "operating_cash_flow", "total_assets",
    "shareholder_equity", "eps_basic",
]
WINDOWS = [1, 3, 5]


def _annual_series(ticker, metric):
    """Return [(period, value)] sorted oldest->newest for annual facts."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT period, value FROM facts WHERE ticker=? AND metric=?
           AND period_type='annual' ORDER BY period""", [ticker, metric]).fetchall()
    conn.close()
    return [(str(p), v) for p, v in rows if v is not None]


def _cagr(begin, end, years):
    """Compound annual growth rate. Handles sign changes gracefully."""
    if begin is None or end is None or years <= 0:
        return None
    if begin <= 0:
        # Can't do CAGR from non-positive base; report simple total change
        if begin == 0:
            return None
        return None
    if end <= 0:
        return None
    return ((end / begin) ** (1 / years) - 1) * 100


def compute_growth(ticker):
    facts = []
    for metric in ITEMS:
        series = _annual_series(ticker, metric)
        if len(series) < 2:
            continue
        latest_period, latest_val = series[-1]
        for w in WINDOWS:
            if len(series) <= w:
                continue
            begin_period, begin_val = series[-(w + 1)]
            cagr = _cagr(begin_val, latest_val, w)
            if cagr is not None:
                facts.append({
                    "ticker": ticker, "metric": f"{metric}_cagr_{w}y",
                    "period": latest_period, "period_type": "growth",
                    "value": round(cagr, 2), "unit": "pct", "source": "growth",
                })
    return facts


def compute_all():
    total = 0
    for ticker in get_tickers():
        facts = compute_growth(ticker)
        write_facts(facts)
        total += len(facts)
        print(f"  {ticker:<6} {len(facts):>3} multi-window growth metrics")
    print(f"\n✅ Extended growth complete: {total} facts.")
    return total


if __name__ == "__main__":
    compute_all()
