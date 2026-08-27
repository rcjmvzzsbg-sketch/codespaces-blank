# config/universe.py
"""Active trading universe: loads the filtered $10B+ non-Chinese cache.
Falls back to a small default if the cache hasn't been built yet."""

from config.universe_builder import load_universe

_DEFAULT = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]


def get_tickers() -> list[str]:
    u = load_universe()
    return [c["ticker"] for c in u] if u else _DEFAULT


def get_universe() -> list[dict]:
    """Full records: ticker, cik, name, market_cap."""
    return load_universe()


def get_cik_map() -> dict:
    """ticker -> cik, for EDGAR (avoids re-fetching the SEC list)."""
    return {c["ticker"]: c["cik"] for c in load_universe()}
