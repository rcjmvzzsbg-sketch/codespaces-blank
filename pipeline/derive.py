# pipeline/derive.py
"""Runs the derivation engine with PERIOD ALIGNMENT — all inputs for a
given ticker's ratios come from the same fiscal year, preventing
mismatched-year distortions (e.g. new profit / old revenue)."""

import metrics  # auto-discovery hook
from core.metrics import DERIVATIONS
from core.database import get_conn, write_facts
from config.universe import get_tickers


def _all_annual(ticker: str) -> dict:
    """Return {metric: {period: value}} for all annual facts of a ticker."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT metric, period, value FROM facts
           WHERE ticker=? AND period_type='annual'""",
        [ticker],
    ).fetchall()
    conn.close()
    data = {}
    for metric, period, value in rows:
        data.setdefault(metric, {})[str(period)] = value
    return data


def _point(ticker: str, metric: str):
    """Latest 'point' value (e.g. price) for a ticker."""
    conn = get_conn()
    row = conn.execute(
        """SELECT value FROM facts WHERE ticker=? AND metric=?
           AND period_type IN ('point','ttm') ORDER BY period DESC LIMIT 1""",
        [ticker, metric],
    ).fetchone()
    conn.close()
    return row[0] if row else None


def derive_ticker(ticker: str, max_passes: int = 6) -> int:
    annual = _all_annual(ticker)

    # Choose the target fiscal year = latest year where 'revenue' exists.
    if "revenue" not in annual or not annual["revenue"]:
        target_year = None
    else:
        target_year = max(annual["revenue"].keys())

    def get_input(name):
        """Prefer the target-year annual value; fall back to point data;
        else the metric's own latest annual."""
        if name in annual:
            if target_year and target_year in annual[name]:
                return annual[name][target_year], target_year
            # fall back to that metric's latest annual
            latest_p = max(annual[name].keys())
            return annual[name][latest_p], latest_p
        pv = _point(ticker, name)
        return (pv, target_year) if pv is not None else (None, None)

    written = 0
    for _ in range(max_passes):
        new_this_pass = 0
        annual = _all_annual(ticker)  # refresh so chained derivations see prior results
        for name, spec in DERIVATIONS.items():
            # skip if already computed for the target year
            if name in annual and target_year and target_year in annual[name]:
                continue
            inputs, periods = [], []
            for inp in spec["inputs"]:
                val, per = get_input(inp)
                inputs.append(val)
                periods.append(per)
            if all(v is None for v in inputs):
                continue
            try:
                value = spec["fn"](*inputs)
            except Exception:
                value = None
            if value is None:
                continue
            out_period = target_year or next((p for p in periods if p), "2026-01-01")
            write_facts([{
                "ticker": ticker, "metric": name,
                "period": out_period, "period_type": "annual",
                "value": value, "unit": spec["unit"], "source": "derived",
            }])
            written += 1
            new_this_pass += 1
        if new_this_pass == 0:
            break
    return written


def derive_all() -> int:
    total = 0
    for ticker in get_tickers():
        n = derive_ticker(ticker)
        total += n
        print(f"  {ticker:<6} {n:>3} derived metrics")
    print(f"\n✅ Derivation complete: {total} computed facts.")
    return total


if __name__ == "__main__":
    derive_all()
