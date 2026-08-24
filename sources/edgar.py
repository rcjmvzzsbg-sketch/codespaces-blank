# sources/edgar.py
"""SEC EDGAR — captures BOTH annual (full-year) and quarterly data points.
Annual: for fiscal-year ratios & growth. Quarterly: for TTM freshness."""

import re
import requests
from core.base_source import BaseSource, register_source
from mappings.xbrl_tags import XBRL_MAP

HEADERS = {"User-Agent": "Stock Screener rcjmvzzsbg@example.com"}
_ANNUAL_FRAME = re.compile(r"^CY\d{4}$")
_YEAREND_FRAME = re.compile(r"^CY\d{4}Q4I$")
_QTR_FRAME = re.compile(r"^CY\d{4}Q[1-4]$")      # e.g. CY2026Q2 (duration)
_QTR_INSTANT = re.compile(r"^CY\d{4}Q[1-4]I$")   # e.g. CY2026Q2I (balance snapshot)


@register_source
class EdgarSource(BaseSource):
    name = "edgar"

    def _get_company_facts(self, cik: str) -> dict:
        cik = str(cik).zfill(10)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _extract(self, facts: dict, tags: list[str], unit: str = "USD"):
        """Return (annual_map, quarterly_map) merged across all candidate tags."""
        us_gaap = facts.get("facts", {}).get("us-gaap", {})
        annual, quarterly = {}, {}
        for tag in reversed(tags):  # priority tag (first) overwrites -> wins
            node = us_gaap.get(tag)
            if not node:
                continue
            units = node.get("units", {})
            points = units.get(unit) or next(iter(units.values()), None)
            if not points:
                continue
            for p in points:
                frame = p.get("frame", "")
                if _ANNUAL_FRAME.match(frame) or _YEAREND_FRAME.match(frame):
                    annual[p["end"]] = p["val"]
                elif _QTR_FRAME.match(frame) or _QTR_INSTANT.match(frame):
                    quarterly[p["end"]] = p["val"]
        return annual, quarterly

    def fetch(self, ticker: str, cik: str | None = None) -> list[dict]:
        if cik is None:
            from mappings.ticker_map import get_cik
            cik = get_cik(ticker)
        if cik is None:
            print(f"[edgar] No CIK found for {ticker}")
            return []
        try:
            facts = self._get_company_facts(cik)
        except requests.RequestException as e:
            print(f"[edgar] {ticker} request failed: {e}")
            return []

        rows = []
        for metric, tags in XBRL_MAP.items():
            annual, quarterly = self._extract(facts, tags)
            for period, value in annual.items():
                rows.append({
                    "ticker": ticker, "metric": metric, "period": period,
                    "period_type": "annual", "value": value,
                    "unit": "USD", "source": "edgar",
                })
            for period, value in quarterly.items():
                rows.append({
                    "ticker": ticker, "metric": metric, "period": period,
                    "period_type": "quarterly", "value": value,
                    "unit": "USD", "source": "edgar",
                })
        return rows
