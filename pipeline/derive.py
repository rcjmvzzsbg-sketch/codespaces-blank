# pipeline/derive.py
"""Runs the derivation engine against stored facts.
Iterates in passes so derived metrics that depend on other
derived metrics resolve automatically."""

from datetime import datetime
import metrics  # triggers auto-discovery of metric modules (if any)
from core.metrics import DERIVATIONS
from core.database import get_conn, write_facts
from config.universe import get_tickers


def _get_annual(ticker: str, metric: str):
    """Latest annual value for a metric (raw or previously derived)."""
    conn = get_conn()
    row = conn.execute(
        """SELECT value, period FROM facts
           WHERE ticker=? AND metric=? AND period_type='annual'
           ORDER BY period DESC LIMIT 1""",
        [ticker, metric],
    ).fetchone()
    conn.close()
    return (row[0], row[1]) if row else (None, None)


def derive_ticker(ticker: str, max_passes: int = 5) -> int:
    """Compute all resolvable derivations for one ticker."""
    written = 0
    for _ in range(max_passes):
        new_this_pass = 0
        for name, spec in DERIVATIONS.items():
            # Skip if we already computed this metric
            existing, _ = _get_annual(ticker, name)
            if existing is not None:
                continue
            # Gather inputs
            inputs, latest_period = [], None
            for inp in spec["inputs"]:
                val, period = _get_annual(ticker, inp)
                inputs.append(val)
                if period and (latest_period is None or period > latest_period):
                    latest_period = period
            if any(v is None for v in inputs):
                continue  # inputs not ready yet (maybe next pass)
            try:
                value = spec["fn"](*inputs)
            except Exception:
                value = None
            if value is None:
                continue
            write_facts([{
                "ticker": ticker, "metric": name,
                "period": latest_period, "period_type": "annual",
                "value": value, "unit": spec["unit"], "source": "derived",
            }])
            written += 1
            new_this_pass += 1
        if new_this_pass == 0:
            break  # nothing new resolved; stop
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
