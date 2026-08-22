# sources/edgar.py
import requests
from core.base_source import BaseSource, register_source

HEADERS = {"User-Agent": "YourName your@email.com"}  # ← put your REAL email

@register_source
class EdgarSource(BaseSource):
    name = "edgar"

    def _get_company_facts(self, cik: str) -> dict:
        cik = str(cik).zfill(10)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def fetch(self, ticker: str) -> list[dict]:
        # TEMPORARY: hardcoded CIK for AAPL so we can test end-to-end.
        # We'll replace this with the ticker_map lookup next.
        cik = "0000320193"  # Apple
        facts = self._get_company_facts(cik)

        rows = []
        # Pull a couple of tags as a proof-of-life
        for tag, metric in [("Revenues", "revenue"), ("Assets", "total_assets")]:
            try:
                points = facts["facts"]["us-gaap"][tag]["units"]["USD"]
                latest = sorted(points, key=lambda x: x["end"])[-1]
                rows.append({
                    "ticker": ticker, "metric": metric,
                    "period": latest["end"], "period_type": "annual",
                    "value": latest["val"], "unit": "USD", "source": "edgar",
                })
            except (KeyError, IndexError):
                continue
        return rows
