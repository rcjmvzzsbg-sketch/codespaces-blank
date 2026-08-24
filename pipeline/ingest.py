# pipeline/ingest.py
"""Loops every ticker through every registered source -> facts table."""

import time
import sources  # triggers auto-discovery of all source plugins
from core.base_source import SOURCES
from core.database import write_facts
from config.universe import get_tickers


def ingest_all(rate_limit_sec: float = 0.15):
    """Run all enabled sources across the full universe."""
    tickers = get_tickers()
    total_rows = 0

    for src in SOURCES.values():
        if not getattr(src, "enabled", True):
            continue
        print(f"\n=== Source: {src.name} ===")
        for ticker in tickers:
            try:
                rows = src.fetch(ticker)
                write_facts(rows)
                total_rows += len(rows)
                print(f"  {ticker:<6} {len(rows):>3} facts")
            except Exception as e:
                print(f"  {ticker:<6} FAILED: {e}")
            time.sleep(rate_limit_sec)  # be polite to free APIs

    print(f"\n✅ Ingest complete: {total_rows} total facts written.")
    return total_rows


if __name__ == "__main__":
    ingest_all()
