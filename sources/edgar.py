# sources/edgar.py
"""SEC EDGAR data source — pulls ALL annual years of fundamentals
for any company via the official XBRL companyfacts API."""

import requests
from core.base_source import BaseSource, register_source
from mappings.xbrl_tags import XBRL_MAP

HEADERS = {"User-Agent": "Stock Screener rcjmvzzsbg@example.com"}


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
        """Return {period_end: value} for every full-year (FY) data point,
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
            # Keep clean full-year figures with a 'frame' (deduped annuals)
            annual = {}
            for p in points:
                if p.get("fp") == "FY" and "frame" in p:
                    annual[p["end"]] = p["val"]
            if not annual:  # fallback: any FY point
                for p in points:
                    if p.get("fp") == "FY":
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
            print(f"[edgar] {ticker} (CIK {cik}) request failed: {e}")
            return []

        rows = []
        for metric, tags in XBRL_MAP.items():
            year_map = self._extract_all_years(facts, tags)
            for period, value in year_map.items():
                rows.append({
                    "ticker": ticker,
                    "metric": metric,
                    "period": period,
                    "period_type": "annual",
                    "value": value,
                    "unit": "USD",
                    "source": "edgar",
                })
        return rows
