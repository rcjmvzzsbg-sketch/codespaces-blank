# metrics/growth.py
"""Growth metrics: YoY and multi-year CAGR for every financial line item.
One function set applied across many metrics = huge data-point multiplier."""

from core.database import get_conn, write_facts
from config.universe import get_tickers

# Line items we compute growth for
GROWTH_TARGETS = [
    "revenue", "net_income", "gross_profit", "operating_income",
    "total_assets", "shareholder_equity", "free_cash_flow",
    "operating_cash_flow", "eps_diluted",
]


def _annual_series(ticker: str, metric: str):
    """Return list of (period, value) sorted oldest->newest."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT period, value FROM facts
           WHERE ticker=? AND metric=? AND period_type='annual'
           ORDER BY period""",
        [ticker, metric],
    ).fetchall()
    conn.close()
    return rows


def _yoy(series):
    if len(series) < 2 or not series[-2][1]:
        return None
    latest, prior = series[-1][1], series[-2][1]
    return (latest - prior) / abs(prior) * 100


def _cagr(series, years):
    if len(series) < years + 1:
        return None
    start = series[-(years + 1)][1]
    end = series[-1][1]
    if not start or start <= 0 or end <= 0:
        return None
    return ((end / start) ** (1 / years) - 1) * 100


def compute_growth(ticker: str) -> list[dict]:
    facts = []
    for metric in GROWTH_TARGETS:
        series = _annual_series(ticker, metric)
        if len(series) < 2:
            continue
        latest_period = series[-1][0]
        computations = {
            f"{metric}_growth_yoy": _yoy(series),
            f"{metric}_cagr_3y": _cagr(series, 3),
            f"{metric}_cagr_5y": _cagr(series, 5),
        }
        for name, value in computations.items():
            if value is not None:
                facts.append({
                    "ticker": ticker, "metric": name,
                    "period": latest_period, "period_type": "annual",
                    "value": value, "unit": "pct", "source": "growth",
                })
    return facts


def compute_all() -> int:
    total = 0
    for ticker in get_tickers():
        facts = compute_growth(ticker)
        write_facts(facts)
        total += len(facts)
        print(f"  {ticker:<6} {len(facts):>3} growth metrics")
    print(f"\n✅ Growth complete: {total} metrics computed.")
    return total


if __name__ == "__main__":
    compute_all()
