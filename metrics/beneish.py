# metrics/beneish.py
"""Beneish M-Score — forensic earnings-manipulation detector (8 variables).
M > -1.78 suggests possible manipulation. Completes the forensic trio
alongside Piotroski (strength) and Altman (solvency)."""

from core.database import get_conn, write_facts
from config.universe import get_tickers


def _two_years(ticker, metric):
    """Return (current, prior) annual values, newest two."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT period, value FROM facts WHERE ticker=? AND metric=?
           AND period_type='annual' ORDER BY period DESC LIMIT 2""",
        [ticker, metric]).fetchall()
    conn.close()
    if len(rows) < 2:
        return None, None
    return rows[0][1], rows[1][1]  # current, prior


def compute_m(ticker):
    def g(metric):
        return _two_years(ticker, metric)

    rev_t, rev_p = g("revenue")
    rec_t, rec_p = g("receivables")
    cogs_t, cogs_p = g("cost_of_revenue")
    ca_t, ca_p = g("current_assets")
    ppe_t, ppe_p = g("ppe_net")
    ta_t, ta_p = g("total_assets")
    dep_t, dep_p = g("depreciation_amortization")
    sga_t, sga_p = g("sga_expense")
    ni_t, ni_p = g("net_income")
    ocf_t, ocf_p = g("operating_cash_flow")
    ltd_t, ltd_p = g("long_term_debt")
    cl_t, cl_p = g("current_liabilities")

    # Need the core set
    if None in (rev_t, rev_p, ta_t, ta_p, ni_t, ocf_t):
        return None

    def safe(n, d):
        return n / d if (n is not None and d not in (None, 0)) else None

    # DSRI: Days Sales in Receivables Index
    dsri = None
    if all(x is not None for x in (rec_t, rev_t, rec_p, rev_p)) and rev_t and rev_p and rec_p:
        dsri = (rec_t / rev_t) / (rec_p / rev_p) if (rec_p / rev_p) else None

    # GMI: Gross Margin Index (prior GM / current GM)
    gmi = None
    if all(x is not None for x in (rev_t, cogs_t, rev_p, cogs_p)) and rev_t and rev_p:
        gm_t = (rev_t - cogs_t) / rev_t
        gm_p = (rev_p - cogs_p) / rev_p
        gmi = gm_p / gm_t if gm_t else None

    # AQI: Asset Quality Index
    aqi = None
    if all(x is not None for x in (ca_t, ppe_t, ta_t, ca_p, ppe_p, ta_p)) and ta_t and ta_p:
        aq_t = 1 - (ca_t + ppe_t) / ta_t
        aq_p = 1 - (ca_p + ppe_p) / ta_p
        aqi = aq_t / aq_p if aq_p else None

    # SGI: Sales Growth Index
    sgi = rev_t / rev_p if rev_p else None

    # DEPI: Depreciation Index
    depi = None
    if all(x is not None for x in (dep_t, ppe_t, dep_p, ppe_p)):
        r_t = safe(dep_t, dep_t + ppe_t)
        r_p = safe(dep_p, dep_p + ppe_p)
        depi = r_p / r_t if (r_t and r_p) else None

    # SGAI: SG&A Index
    sgai = None
    if all(x is not None for x in (sga_t, rev_t, sga_p, rev_p)) and rev_t and rev_p:
        sgai = (sga_t / rev_t) / (sga_p / rev_p) if (sga_p / rev_p) else None

    # LVGI: Leverage Index
    lvgi = None
    if all(x is not None for x in (ltd_t, cl_t, ta_t, ltd_p, cl_p, ta_p)) and ta_t and ta_p:
        lev_t = (ltd_t + cl_t) / ta_t
        lev_p = (ltd_p + cl_p) / ta_p
        lvgi = lev_t / lev_p if lev_p else None

    # TATA: Total Accruals to Total Assets
    tata = None
    if all(x is not None for x in (ni_t, ocf_t, ta_t)) and ta_t:
        tata = (ni_t - ocf_t) / ta_t

    # Default neutral values (1.0 for indices, 0 for TATA) where missing
    dsri = dsri if dsri is not None else 1.0
    gmi = gmi if gmi is not None else 1.0
    aqi = aqi if aqi is not None else 1.0
    sgi = sgi if sgi is not None else 1.0
    depi = depi if depi is not None else 1.0
    sgai = sgai if sgai is not None else 1.0
    lvgi = lvgi if lvgi is not None else 1.0
    tata = tata if tata is not None else 0.0

    # Beneish 8-variable model
    m = (-4.84 + 0.920*dsri + 0.528*gmi + 0.404*aqi + 0.892*sgi
         + 0.115*depi - 0.172*sgai + 4.679*tata - 0.327*lvgi)
    return m


def compute_all():
    total = 0
    for ticker in get_tickers():
        m = compute_m(ticker)
        if m is None:
            print(f"  {ticker:<6} insufficient data")
            continue
        flag = "⚠️ POSSIBLE MANIPULATION" if m > -1.78 else "✓ clean"
        write_facts([{
            "ticker": ticker, "metric": "beneish_m", "period": "2026-08-24",
            "period_type": "score", "value": round(m, 3),
            "unit": "score", "source": "scores",
        }])
        total += 1
        print(f"  {ticker:<6} M-Score: {m:>7.3f}   {flag}")
    print(f"\n✅ Beneish complete: {total} facts.")
    return total


if __name__ == "__main__":
    compute_all()
