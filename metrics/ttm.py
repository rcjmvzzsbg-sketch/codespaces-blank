# metrics/ttm.py
"""TTM anchored to annual, with DATE-MATCHED netting:
TTM = latest_annual + sum(new quarters after FY-end)
      - sum(each new quarter's SAME quarter one year earlier).
Handles missing fiscal-Q4 (embedded in 10-K) and any fiscal calendar."""

from datetime import date, timedelta
from core.database import get_conn, write_facts
from config.universe import get_tickers

FLOW = ["revenue", "net_income", "gross_profit", "operating_income",
        "operating_cash_flow", "capex", "cost_of_revenue", "rd_expense",
        "interest_expense", "income_tax", "pretax_income"]
STOCK = ["total_assets", "shareholder_equity", "total_debt", "cash",
         "current_assets", "current_liabilities", "shares_outstanding"]


def _d(s):
    y, m, dd = map(int, str(s).split("-")); return date(y, m, dd)


def _annual_latest(ticker, metric):
    conn = get_conn()
    r = conn.execute("""SELECT period,value FROM facts WHERE ticker=? AND metric=?
                        AND period_type='annual' ORDER BY period DESC LIMIT 1""",
                     [ticker, metric]).fetchone()
    conn.close()
    return (str(r[0]), r[1]) if r else (None, None)


def _quarters(ticker, metric):
    conn = get_conn()
    rows = conn.execute("""SELECT period,value FROM facts WHERE ticker=? AND metric=?
                           AND period_type='quarterly' ORDER BY period""",
                        [ticker, metric]).fetchall()
    conn.close()
    return [(str(p), v) for p, v in rows if v is not None]


def _ttm_flow(ticker, metric):
    a_period, a_value = _annual_latest(ticker, metric)
    if a_value is None:
        return None, None
    qs = _quarters(ticker, metric)
    if not qs:
        return a_value, a_period

    ap = _d(a_period)
    new_q = [(p, v) for p, v in qs if _d(p) > ap]
    if not new_q:
        return a_value, a_period  # annual IS the freshest 12 months

    total = a_value
    for p, v in new_q:
        year_ago = _d(p) - timedelta(days=365)
        best, best_diff = None, 9999
        for pp, vv in qs:
            diff = abs((_d(pp) - year_ago).days)
            if diff < best_diff:
                best_diff, best = diff, (pp, vv)
        if best is None or best_diff > 50:   # no clean year-ago match
            return None, None
        total += v - best[1]                 # add new, roll off year-ago
    return total, new_q[-1][0]


def compute_ttm(ticker):
    facts, vals, latest_period = [], {}, None
    for metric in FLOW:
        ttm, period = _ttm_flow(ticker, metric)
        if ttm is None:
            continue
        vals[metric] = ttm
        latest_period = period or latest_period
        facts.append({"ticker": ticker, "metric": f"{metric}_ttm", "period": period,
                      "period_type": "ttm", "value": ttm, "unit": "USD", "source": "ttm"})

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
            facts.append({"ticker": ticker, "metric": name, "period": latest_period,
                          "period_type": "ttm", "value": round(value, 4),
                          "unit": unit, "source": "ttm"})

    rev, ni = vals.get("revenue"), vals.get("net_income")
    gp, oi = vals.get("gross_profit"), vals.get("operating_income")
    ocf, capex = vals.get("operating_cash_flow"), vals.get("capex")
    equity, assets = vals.get("shareholder_equity"), vals.get("total_assets")
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

    conn = get_conn()
    mc = conn.execute("""SELECT value FROM facts WHERE ticker=? AND metric='market_cap'
                         ORDER BY period DESC LIMIT 1""", [ticker]).fetchone()
    conn.close()
    mcap = mc[0] if mc else None
    if ni and ni > 0:
        if mcap: add("pe_ttm", mcap / ni, "ratio")
        if shares: add("eps_ttm_actual", ni / shares, "USD")
    return facts


def _purge_ttm():
    conn = get_conn(); conn.execute("DELETE FROM facts WHERE source='ttm'"); conn.close()


def compute_all():
    _purge_ttm()
    total = 0
    for ticker in get_tickers():
        f = compute_ttm(ticker); write_facts(f); total += len(f)
        print(f"  {ticker:<6} {len(f):>3} TTM metrics")
    print(f"\n✅ TTM complete: {total} facts.")
    return total


if __name__ == "__main__":
    compute_all()
