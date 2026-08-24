# sources/edgar.py
"""SEC EDGAR data source — pulls fundamental financials for any company
via the official XBRL companyfacts API."""

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

    def _extract_metric(self, facts: dict, tags: list[str], unit: str = "USD"):
        us_gaap = facts.get("facts", {}).get("us-gaap", {})
        for tag in tags:
            node = us_gaap.get(tag)
            if not node:
                continue
            units = node.get("units", {})
            points = units.get(unit) or next(iter(units.values()), None)
            if not points:
                continue
            annual = [p for p in points if p.get("fp") == "FY" and "frame" in p]
            if not annual:
                annual = [p for p in points if p.get("fp") == "FY"]
            if not annual:
                annual = points
            latest = sorted(annual, key=lambda x: x["end"])[-1]
            return latest["val"], latest["end"]
        return None, None

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
            value, period = self._extract_metric(facts, tags)
            if value is not None:
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
