# mappings/ticker_map.py
"""Ticker <-> CIK mapping, sourced from SEC's official free file.
Downloads once, caches locally, then serves instant lookups."""

import json
import requests
from pathlib import Path

HEADERS = {"User-Agent": "Stock Screener rcjmvzzsbg@example.com"}
CACHE = Path(__file__).parent / "_ticker_cik_cache.json"
SEC_URL = "https://www.sec.gov/files/company_tickers.json"

_MAP = None  # in-memory cache


def _download() -> dict:
    """Fetch SEC's ticker->CIK file and normalize into {TICKER: cik10}."""
    resp = requests.get(SEC_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    raw = resp.json()  # {"0": {"cik_str": 320193, "ticker": "AAPL", ...}, ...}
    mapping = {}
    for entry in raw.values():
        ticker = entry["ticker"].upper()
        cik10 = str(entry["cik_str"]).zfill(10)
        mapping[ticker] = cik10
    CACHE.write_text(json.dumps(mapping))
    return mapping


def _load() -> dict:
    """Load map from memory, then disk cache, then download as last resort."""
    global _MAP
    if _MAP is not None:
        return _MAP
    if CACHE.exists():
        _MAP = json.loads(CACHE.read_text())
    else:
        _MAP = _download()
    return _MAP


def get_cik(ticker: str) -> str | None:
    """Return 10-digit zero-padded CIK for a ticker, or None if unknown."""
    return _load().get(ticker.upper())


def refresh():
    """Force re-download of the SEC ticker file (run occasionally)."""
    global _MAP
    _MAP = _download()
    return len(_MAP)
