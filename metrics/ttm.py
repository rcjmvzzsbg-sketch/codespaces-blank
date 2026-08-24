# metrics/ttm.py
"""Trailing-Twelve-Month metrics, ANCHORED TO THE ANNUAL figure to correctly
handle the missing fiscal-Q4 (companies embed Q4 in the 10-K, not a 10-Q).

TTM_flow = latest_annual + (quarters after FY-end) - (same quarters prior year)
The missing Q4 is already inside the annual, so we never need it."""

from core.database import get_conn, write_facts
from config.universe import get_tickers

FLOW = [
    "revenue", "net_income", "gross_profit", "operating_income",
    "operating_cash_flow", "capex", "cost_of_revenue",
    "rd_expense", "interest_expense", "income_tax", "pretax_income",
]
STOCK = [
    "total_assets", "shareholder_equity", "total_debt", "cash",
    "current_assets", "current_liabilities", "shares_outstanding",
]


def _annual_latest(ticker, metric):
    conn = get_conn()
    r = conn.execute(
        """SELECT period, value FROM facts WHERE ticker=? AND metric=?
           AND period_type='annual' ORDER BY period DESC LIMIT 1""",
        [ticker, metric]).fetchone()
    conn.close()
    return (str(r[0]), r[1]) if r else (None, None)


def _quarters(ticker, metric):
    conn = get_conn()
    rows = conn.execute(
        """SELECT period, value FROM facts WHERE ticker=? AND metric=?
           AND period_type='quarterly' ORDER BY period""", [ticker, metric]).fetchall()
    conn.close()
    return [(str(p), v) for p, v in rows if v is not None]


def _point(ticker, metric):
    conn = get_conn()
    r = conn.execute(
        """SELECT value FROM facts WHERE ticker=? AND metric=?
           AND period_type IN ('point','ttm') ORDER BY period DESC LIMIT 1""",
        [ticker, metric]).fetchone()
    conn.close()
    return r[0] if r else None


def _ttm_flow(ticker, metric):
    """Annual-anchored TTM for a flow metric. Returns (value, period) or (None, None)."""
    a_period, a_value = _annual_latest(ticker, metric)
    if a_value is None:
        return None, None
    qs = _quarters(ticker, metric)
    if not qs:
        return a_value, a_period  # only annual available -> use it

    # Quarters strictly AFTER the fiscal year-end = the "new" ones.
    new_q = [(p, v) for p, v in qs if p > a_period]
    if not new_q:
        return a_value, a_period  # annual IS the freshest 12 months

    k = len(new_q)
    # The k quarters ending on/before FY-end, one year earlier = "old" ones.
    prior = [(p, v) for p, v in qs if p <= a_period]
    if len(prior) < k:
        return None, None  # not enough history to net out cleanly
    old_q = prior[-k:]

    ttm = a_value + sum(v for _, v in new_q) - sum(v for _, v in old_q)
    latest_period = new_q[-1][0]
    return ttm, latest_period


def compute_ttm(ticker):
    facts = []
    vals = {}
    latest_period = None

    for metric in FLOW:
        ttm, period = _ttm_flow(ticker, metric)
        if ttm is None:
            continue
        vals[metric] = ttm
        latest_period = period or latest_period
        facts.append({
            "ticker": ticker, "metric": f"{metric}_ttm", "period": period,
            "period_type": "ttm", "value": ttm, "unit": "USD", "source": "ttm",
        })

    # Balance-sheet: most recent quarter (or annual fallback)
    for metric in STOCK:
        qs = _quarters(ticker, metric)
        if qs:
            vals[metric] = qs[-1][1]
        else:
            _, av = _annual_latest(ticker, metric)
            if av is not None:
                vals[metric] = av

    if not latest_period:
        return facts

    def add(name, value, unit="pct"):
        if value is not None:
            facts.append({
                "ticker": ticker, "metric": name, "period": latest_period,
                "period_type": "ttm", "value": round(value, 4),
                "unit": unit, "source": "ttm",
            })

    rev = vals.get("revenue"); ni = vals.get("net_income")
    gp = vals.get("gross_profit"); oi = vals.get("operating_income")
    ocf = vals.get("operating_cash_flow"); capex = vals.get("capex")
    equity = vals.get("shareholder_equity"); assets = vals.get("total_assets")
    shares = vals.get("shares_outstanding")

    if rev:
        if ni is not None: add("net_margin_ttm", ni / rev * 100)
        if gp is not None: add("gross_margin_ttm", gp / rev * 100)
        if oi is not None: add("operating_margin_ttm", oi / rev * 100)
    if ni and equity: add("roe_ttm", ni / equity * 100)
    if ni and assets: add("roa_ttm", ni / assets * 100)

    if ocf is not None and capex is not None:
        fcf = ocf - abs(capex)
        add("free_cash_flow_ttm", fcf, "USD")
        if rev: add("fcf_margin_ttm", fcf / rev * 100)

    # P/E via market_cap (dodges the missing quarterly-shares problem)
    mcap = _point(ticker, "market_cap")
    if ni and ni > 0:
        if mcap: add("pe_ttm", mcap / ni, "ratio")
        if shares: add("eps_ttm_actual", ni / shares, "USD")

    return facts


def _purge_ttm():
    conn = get_conn()
    conn.execute("DELETE FROM facts WHERE source='ttm'")
    conn.close()


def compute_all():
    _purge_ttm()  # clear stale TTM rows so periods don't duplicate
    total = 0
    for ticker in get_tickers():
        facts = compute_ttm(ticker)
        write_facts(facts)
        total += len(facts)
        print(f"  {ticker:<6} {len(facts):>3} TTM metrics")
    print(f"\n✅ TTM complete: {total} facts.")
    return total


if __name__ == "__main__":
    compute_all()
