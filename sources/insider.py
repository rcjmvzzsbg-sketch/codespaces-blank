# sources/insider.py
"""SEC Form 4 insider transactions — the unique free predictive edge.
Aggregates open-market insider buys (code P) vs sells (code S)."""

import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from core.base_source import BaseSource, register_source

HEADERS = {"User-Agent": "Stock Screener rcjmvzzsbg@example.com"}
LOOKBACK_DAYS = 180
MAX_FILINGS = 40


@register_source
class InsiderSource(BaseSource):
    name = "insider"

    def _recent_form4(self, cik: str) -> list[dict]:
        cik10 = str(cik).zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{cik10}.json"
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        recent = r.json().get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accns = recent.get("accessionNumber", [])
        docs = recent.get("primaryDocument", [])
        dates = recent.get("filingDate", [])
        cutoff = (datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)).date()

        out = []
        for form, accn, doc, date in zip(forms, accns, docs, dates):
            if form != "4":
                continue
            try:
                fdate = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                continue
            if fdate < cutoff:
                continue
            out.append({"accession": accn, "doc": doc, "date": date})
            if len(out) >= MAX_FILINGS:
                break
        return out

    def _parse_form4(self, cik: str, accession: str, doc: str) -> list[dict]:
        cik_int = int(cik)
        accn_nodash = accession.replace("-", "")
        # Strip the XSL-render prefix (e.g. "xslF345X06/") to get RAW xml.
        raw_doc = doc.split("/")[-1]
        url = (f"https://www.sec.gov/Archives/edgar/data/"
               f"{cik_int}/{accn_nodash}/{raw_doc}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            root = ET.fromstring(r.content)
        except Exception:
            return []

        txns = []
        # Raw Form 4 XML (root = ownershipDocument) has NO namespace.
        for t in root.findall(".//nonDerivativeTransaction"):
            code_el = t.find(".//transactionCoding/transactionCode")
            shares_el = t.find(".//transactionAmounts/transactionShares/value")
            price_el = t.find(".//transactionAmounts/transactionPricePerShare/value")
            if code_el is None or shares_el is None:
                continue
            code = (code_el.text or "").strip()
            try:
                shares = float(shares_el.text or 0)
                price = float(price_el.text) if (price_el is not None and price_el.text) else 0.0
            except ValueError:
                continue
            txns.append({"code": code, "shares": shares,
                         "price": price, "value": shares * price})
        return txns

    def fetch(self, ticker: str, cik: str | None = None) -> list[dict]:
        if cik is None:
            from mappings.ticker_map import get_cik
            cik = get_cik(ticker)
        if cik is None:
            return []
        try:
            filings = self._recent_form4(cik)
        except requests.RequestException as e:
            print(f"[insider] {ticker} submissions failed: {e}")
            return []

        buy_shares = sell_shares = buy_value = sell_value = 0.0
        buy_count = sell_count = 0
        for f in filings:
            for txn in self._parse_form4(cik, f["accession"], f["doc"]):
                if txn["code"] == "P":
                    buy_shares += txn["shares"]; buy_value += txn["value"]; buy_count += 1
                elif txn["code"] == "S":
                    sell_shares += txn["shares"]; sell_value += txn["value"]; sell_count += 1
            time.sleep(0.05)

        total = buy_value + sell_value
        sentiment = (buy_value / total) if total > 0 else 0.5
        today = datetime.utcnow().strftime("%Y-%m-%d")

        def fact(m, v, u):
            return {"ticker": ticker, "metric": m, "period": today,
                    "period_type": "point", "value": v, "unit": u, "source": "insider"}

        return [
            fact("insider_buy_count", buy_count, "count"),
            fact("insider_sell_count", sell_count, "count"),
            fact("insider_net_shares", buy_shares - sell_shares, "shares"),
            fact("insider_buy_value", buy_value, "USD"),
            fact("insider_sell_value", sell_value, "USD"),
            fact("insider_sentiment", round(sentiment * 100, 1), "pct"),
        ]
