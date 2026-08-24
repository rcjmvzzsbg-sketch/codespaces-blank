# metrics/scores.py
"""Piotroski F-Score (0-9 financial strength) and Altman Z-Score
(bankruptcy risk). Pure computation on stored facts — no new sources."""

from core.database import get_conn, write_facts
from config.universe import get_tickers


def _annual(ticker):
    """Return {metric: {year: value}} for a ticker's annual facts."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT metric, period, value FROM facts WHERE ticker=? AND period_type='annual'",
        [ticker]).fetchall()
    conn.close()
    d = {}
    for m, p, v in rows:
        d.setdefault(m, {})[str(p)] = v
    return d


def _yrs(series):
    """Sorted year keys, oldest->newest."""
    return sorted(series.keys()) if series else []


def _latest_two(d, metric):
    """Return (current, prior) values for a metric, or (None, None)."""
    s = d.get(metric, {})
    ys = _yrs(s)
    if len(ys) >= 2:
        return s[ys[-1]], s[ys[-2]]
    if len(ys) == 1:
        return s[ys[-1]], None
    return None, None


def piotroski(ticker, d):
    """9-point F-score. +1 per criterion passed."""
    score = 0
    ni, ni_p = _latest_two(d, "net_income")
    ta, ta_p = _latest_two(d, "total_assets")
    ocf, _ = _latest_two(d, "operating_cash_flow")
    ltd, ltd_p = _latest_two(d, "long_term_debt")
    ca, ca_p = _latest_two(d, "current_assets")
    cl, cl_p = _latest_two(d, "current_liabilities")
    rev, rev_p = _latest_two(d, "revenue")
    gp, gp_p = _latest_two(d, "gross_profit")
    shares, shares_p = _latest_two(d, "shares_outstanding")

    # --- Profitability (4 points) ---
    if ni and ni > 0: score += 1                      # 1. positive net income
    if ocf and ocf > 0: score += 1                    # 2. positive operating CF
    # 3. ROA improving
    if ni and ta and ni_p and ta_p:
        if (ni / ta) > (ni_p / ta_p): score += 1
    # 4. quality of earnings (OCF > net income)
    if ocf and ni and ocf > ni: score += 1

    # --- Leverage/Liquidity (3 points) ---
    # 5. lower long-term debt ratio
    if ltd is not None and ta and ltd_p is not None and ta_p:
        if (ltd / ta) < (ltd_p / ta_p): score += 1
    # 6. higher current ratio
    if ca and cl and ca_p and cl_p:
        if (ca / cl) > (ca_p / cl_p): score += 1
    # 7. no dilution (shares flat or down)
    if shares and shares_p and shares <= shares_p: score += 1

    # --- Efficiency (2 points) ---
    # 8. higher gross margin
    if gp and rev and gp_p and rev_p:
        if (gp / rev) > (gp_p / rev_p): score += 1
    # 9. higher asset turnover
    if rev and ta and rev_p and ta_p:
        if (rev / ta) > (rev_p / ta_p): score += 1

    return score


def altman_z(ticker, d):
    """Altman Z = 1.2A + 1.4B + 3.3C + 0.6D + 1.0E."""
    def latest(m):
        s = d.get(m, {})
        ys = _yrs(s)
        return s[ys[-1]] if ys else None

    ta = latest("total_assets")
    if not ta:
        return None
    ca = latest("current_assets") or 0
    cl = latest("current_liabilities") or 0
    re = latest("retained_earnings") or 0
    ebit = latest("operating_income") or 0   # EBIT ~ operating income
    tl = latest("total_liabilities")
    rev = latest("revenue") or 0

    # market cap: latest 'point' fact
    conn = get_conn()
    mc = conn.execute(
        "SELECT value FROM facts WHERE ticker=? AND metric='market_cap' ORDER BY period DESC LIMIT 1",
        [ticker]).fetchone()
    conn.close()
    market_cap = mc[0] if mc else None
    if not tl or not market_cap:
        return None

    A = (ca - cl) / ta          # working capital / total assets
    B = re / ta                 # retained earnings / total assets
    C = ebit / ta               # EBIT / total assets
    D = market_cap / tl         # market cap / total liabilities
    E = rev / ta                # sales / total assets
    return 1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E


def compute_all():
    total = 0
    for ticker in get_tickers():
        d = _annual(ticker)
        if not d:
            continue
        f = piotroski(ticker, d)
        z = altman_z(ticker, d)
        facts = [{
            "ticker": ticker, "metric": "piotroski_f", "period": "2026-08-24",
            "period_type": "score", "value": float(f), "unit": "score", "source": "scores",
        }]
        if z is not None:
            facts.append({
                "ticker": ticker, "metric": "altman_z", "period": "2026-08-24",
                "period_type": "score", "value": round(z, 2), "unit": "score", "source": "scores",
            })
        write_facts(facts)
        total += len(facts)
        zt = f"{z:.2f}" if z is not None else "n/a"
        print(f"  {ticker:<6} Piotroski F: {f}/9   Altman Z: {zt}")
    print(f"\n✅ Scores complete: {total} facts.")
    return total


if __name__ == "__main__":
    compute_all()
