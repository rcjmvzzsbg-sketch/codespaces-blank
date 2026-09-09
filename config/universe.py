# config/universe.py
"""Active trading universe: loads the filtered $10B+ non-Chinese cache.
Falls back to a small default if the cache hasn't been built yet."""

from config.universe_builder import load_universe
import json as _json, os as _os

def _excluded() -> set:
    """Hard-coded ethical exclusions. Applied to ALL universe access."""
    p = "config/excluded_tickers.json"
    return set(_json.load(open(p))) if _os.path.exists(p) else set()


_DEFAULT = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]


def get_tickers() -> list[str]:
    u = load_universe()
    ex = _excluded()
    return [c["ticker"] for c in u if c["ticker"] not in ex] if u else _DEFAULT


def get_universe() -> list[dict]:
    """Full records: ticker, cik, name, market_cap."""
    ex = _excluded()
    return [c for c in load_universe() if c["ticker"] not in ex]


def get_cik_map() -> dict:
    """ticker -> cik, for EDGAR (avoids re-fetching the SEC list)."""
    ex = _excluded()
    return {c["ticker"]: c["cik"] for c in load_universe() if c["ticker"] not in ex}
