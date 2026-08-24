# metrics/ttm.py
"""Trailing-Twelve-Month metrics: sum last 4 quarters for flow items,
use latest quarter for balance-sheet items, compute fresh TTM ratios.
Runs ALONGSIDE annual metrics so you can compare fiscal-year vs TTM."""

from core.database import get_conn, write_facts
from config.universe import get_tickers

# Flow metrics: accumulate over time -> SUM trailing 4 quarters
FLOW = [
    "revenue", "net_income", "gross_profit", "operating_income",
    "operating_cash_flow", "capex", "cost_of_revenue",
    "rd_expense", "interest_expense", "income_tax", "pretax_income",
]
# Stock metrics: point-in-time -> use MOST RECENT quarter
STOCK = [
    "total_assets", "shareholder_equity", "total_debt", "cash",
    "current_assets", "current_liabilities", "shares_outstanding",
]


def _quarters(ticker, metric):
    """Sorted [(period, value)] of quarterly facts, oldest->newest."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT period, value FROM facts
           WHERE ticker=? AND metric=? AND period_type='quarterly'
           ORDER BY period""", [ticker, metric]).fetchall()
    conn.close()
    return [(str(p), v) for p, v in rows]


def _point(ticker, metric):
    conn = get_conn()
    r = conn.execute(
        """SELECT value FROM facts WHERE ticker=? AND metric=?
           AND period_type IN ('point','ttm') ORDER BY period DESC LIMIT 1""",
        [ticker, metric]).fetchone()
    conn.close()
    return r[0] if r else None


def compute_ttm(ticker):
    facts = []
    latest_period = None
    ttm_vals = {}

    # --- Flow metrics: sum trailing 4 quarters ---
    for metric in FLOW:
        qs = _quarters(ticker, metric)
        if len(qs) < 4:
            continue
        last4 = qs[-4:]
        total = sum(v for _, v in last4 if v is not None)
        if len([v for _, v in last4 if v is not None]) < 4:
            continue  # need all 4 quarters for a clean TTM
        ttm_vals[metric] = total
        latest_period = last4[-1][0]
        facts.append({
            "ticker": ticker, "metric": f"{metric}_ttm", "period": last4[-1][0],
            "period_type": "ttm", "value": total, "unit": "USD", "source": "ttm",
        })

    # --- Stock metrics: most recent quarter ---
    for metric in STOCK:
        qs = _quarters(ticker, metric)
        if qs:
            ttm_vals[metric] = qs[-1][1]

    if not latest_period:
        return facts  # not enough quarterly data

    # --- Fresh TTM ratios ---
    def add(name, value, unit="pct"):
        if value is not None:
            facts.append({
                "ticker": ticker, "metric": name, "period": latest_period,
                "period_type": "ttm", "value": round(value, 4),
                "unit": unit, "source": "ttm",
            })

    rev = ttm_vals.get("revenue")
    ni = ttm_vals.get("net_income")
    gp = ttm_vals.get("gross_profit")
    oi = ttm_vals.get("operating_income")
    ocf = ttm_vals.get("operating_cash_flow")
    capex = ttm_vals.get("capex")
    shares = ttm_vals.get("shares_outstanding")
    equity = ttm_vals.get("shareholder_equity")
    assets = ttm_vals.get("total_assets")

    if rev:
        if ni is not None: add("net_margin_ttm", ni / rev * 100)
        if gp is not None: add("gross_margin_ttm", gp / rev * 100)
        if oi is not None: add("operating_margin_ttm", oi / rev * 100)
    if ni and equity: add("roe_ttm", ni / equity * 100)
    if ni and assets: add("roa_ttm", ni / assets * 100)

    # TTM free cash flow + margin
    if ocf is not None and capex is not None:
        fcf_ttm = ocf - abs(capex)
        add("free_cash_flow_ttm", fcf_ttm, "USD")
        if rev: add("fcf_margin_ttm", fcf_ttm / rev * 100)

    # TTM EPS + P/E (needs price)
    price = _point(ticker, "price")
    if ni and shares:
        eps = ni / shares
        add("eps_ttm_actual", eps, "USD")
        if price and eps > 0:
            add("pe_ttm", price / eps, "ratio")

    return facts


def compute_all():
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
