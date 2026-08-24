# sources/fred.py
"""FRED macro indicators via the official API (fast JSON, free key).
Writes to the 'macro' table (ticker-independent economic series)."""

import os
import requests
from core.base_source import BaseSource, register_source
from core.database import get_conn

API_KEY = os.environ.get("FRED_API_KEY", "")
BASE = "https://api.stlouisfed.org/fred/series/observations"

SERIES = {
    "GDP":      "Gross Domestic Product",
    "CPIAUCSL": "Consumer Price Index",
    "DGS10":    "10-Year Treasury Yield",
    "DGS2":     "2-Year Treasury Yield",
    "UNRATE":   "Unemployment Rate",
    "FEDFUNDS": "Federal Funds Rate",
    "T10Y2Y":   "10Y-2Y Yield Spread",
    "VIXCLS":   "VIX Volatility Index",
}


@register_source
class FredSource(BaseSource):
    name = "fred"

    def _get_series(self, series_id: str) -> list[tuple]:
        params = {
            "series_id": series_id,
            "api_key": API_KEY,
            "file_type": "json",
            # only pull recent history to keep it fast
            "observation_start": "2015-01-01",
        }
        resp = requests.get(BASE, params=params, timeout=20)
        resp.raise_for_status()
        obs = resp.json().get("observations", [])
        rows = []
        for o in obs:
            if o["value"] == ".":       # FRED missing-value marker
                continue
            try:
                rows.append((series_id, o["date"], float(o["value"])))
            except ValueError:
                continue
        return rows

    def _write_macro(self, rows: list[tuple]):
        if not rows:
            return
        conn = get_conn()
        conn.executemany(
            """INSERT OR REPLACE INTO macro (series_id, date, value)
               VALUES (?, ?, ?)""",
            rows,
        )
        conn.close()

    def fetch(self, ticker: str = None) -> list[dict]:
        # Universe-wide; only run once (on first ticker) per ingest
        from config.universe import get_tickers
        if ticker is not None and ticker != get_tickers()[0]:
            return []

        if not API_KEY:
            print("  [fred] No FRED_API_KEY set — skipping. "
                  "Get a free key at fredaccount.stlouisfed.org/apikeys")
            return []

        for series_id in SERIES:
            try:
                rows = self._get_series(series_id)
                self._write_macro(rows)
                print(f"  [fred] {series_id}: {len(rows)} observations")
            except Exception as e:
                print(f"  [fred] {series_id} failed: {e}")
        return []
