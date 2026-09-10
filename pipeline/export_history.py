# pipeline/export_history.py
"""Export FULL historical time series (prices + fundamentals) so the
ML repo has real data to train on. Unlike export.py (latest snapshot
only), this preserves every date/period — required for computing
forward returns at multiple horizons."""

import os
from core.database import get_conn

OUT = "output/history"


def export_history():
    os.makedirs(OUT, exist_ok=True)
    conn = get_conn()

    print("Exporting full price history...")
    conn.execute(f"""
        COPY (SELECT * FROM prices ORDER BY ticker, date)
        TO '{OUT}/prices.parquet' (FORMAT PARQUET)
    """)

    print("Exporting full fundamentals history...")
    conn.execute(f"""
        COPY (SELECT * FROM facts ORDER BY ticker, metric, period)
        TO '{OUT}/facts.parquet' (FORMAT PARQUET)
    """)

    conn.close()

    prices_size = os.path.getsize(f"{OUT}/prices.parquet") / 1e6
    facts_size = os.path.getsize(f"{OUT}/facts.parquet") / 1e6
    print(f"✅ {OUT}/prices.parquet ({prices_size:.1f} MB)")
    print(f"✅ {OUT}/facts.parquet ({facts_size:.1f} MB)")


if __name__ == "__main__":
    export_history()
