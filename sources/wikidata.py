# sources/wikidata.py
"""Sector/industry metadata via yfinance (more reliable than Wikidata's
sparse ticker coverage). Populates 'securities' for sector-relative ranking."""

import yfinance as yf
from core.base_source import BaseSource, register_source
from core.database import get_conn


@register_source
class WikidataSource(BaseSource):
    name = "wikidata"  # keep name for pipeline compatibility

    def _write_security(self, ticker, info):
        from mappings.ticker_map import get_cik
        conn = get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO securities
               (ticker, cik, name, sector, industry, is_active, updated_at)
               VALUES (?, ?, ?, ?, ?, TRUE, current_timestamp)""",
            [ticker, get_cik(ticker),
             info.get("longName") or info.get("shortName"),
             info.get("sector"), info.get("industry")],
        )
        conn.close()

    def fetch(self, ticker: str) -> list[dict]:
        try:
            info = yf.Ticker(ticker).info
        except Exception as e:
            print(f"  [wikidata] {ticker} failed: {e}")
            return []
        if info:
            self._write_security(ticker, info)
            print(f"  [wikidata] {ticker}: {info.get('sector')} / {info.get('industry')}")
        return []
