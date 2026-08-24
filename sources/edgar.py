# sources/edgar.py
"""SEC EDGAR — pulls ONLY true annual (full fiscal year) fundamentals."""

import re
import requests
from core.base_source import BaseSource, register_source
from mappings.xbrl_tags import XBRL_MAP

HEADERS = {"User-Agent": "Stock Screener rcjmvzzsbg@example.com"}

# Full-year duration frames: "CY2023"  |  Year-end instant frames: "CY2023Q4I"
_ANNUAL_FRAME = re.compile(r"^CY\d{4}$")
_YEAREND_FRAME = re.compile(r"^CY\d{4}Q4I$")


@register_source
class EdgarSource(BaseSource):
    name = "edgar"

    def _get_company_facts(self, cik: str) -> dict:
        cik = str(cik).zfill(10)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _extract_all_years(self, facts: dict, tags: list[str], unit: str = "USD"):
        """Return {period_end: value} for TRUE annual data points only,
        using the first tag that has data."""
        us_gaap = facts.get("facts", {}).get("us-gaap", {})
        for tag in tags:
            node = us_gaap.get(tag)
            if not node:
                continue
            units = node.get("units", {})
            points = units.get(unit) or next(iter(units.values()), None)
            if not points:
                continue
            annual = {}
            for p in points:
                frame = p.get("frame", "")
                # Keep only full-year durations OR year-end instants
                if _ANNUAL_FRAME.match(frame) or _YEAREND_FRAME.match(frame):
                    annual[p["end"]] = p["val"]
            if annual:
                return annual
        return {}

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
            for period, value in self._extract_all_years(facts, tags).items():
                rows.append({
                    "ticker": ticker, "metric": metric,
                    "period": period, "period_type": "annual",
                    "value": value, "unit": "USD", "source": "edgar",
                })
        return rows
