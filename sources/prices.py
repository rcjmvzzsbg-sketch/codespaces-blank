# sources/prices.py
"""Historical OHLCV via yfinance (Yahoo Finance). Replaces Stooq,
which now requires JS proof-of-work and is unusable programmatically."""

import yfinance as yf
from core.base_source import BaseSource, register_source
from core.database import get_conn


@register_source
class PriceSource(BaseSource):
    name = "prices"

    def _write_prices(self, ticker: str, df):
        conn = get_conn()
        rows = []
        for idx, r in df.iterrows():
            rows.append((
                ticker,
                idx.strftime("%Y-%m-%d"),
                float(r["Open"]), float(r["High"]),
                float(r["Low"]), float(r["Close"]),
                int(r["Volume"]) if r["Volume"] == r["Volume"] else 0,
            ))
        conn.executemany(
            """INSERT OR REPLACE INTO prices
               (ticker, date, open, high, low, close, volume)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        conn.close()

    def fetch(self, ticker: str) -> list[dict]:
        try:
            df = yf.download(
                ticker, period="5y", interval="1d",
                progress=False, auto_adjust=True,
            )
        except Exception as e:
            print(f"[prices] {ticker} download failed: {e}")
            return []

        if df is None or df.empty:
            print(f"[prices] no data for {ticker}")
            return []

        # yfinance sometimes returns multi-index columns; flatten them
        if hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
            df.columns = df.columns.get_level_values(0)

        self._write_prices(ticker, df)

        last_date = df.index[-1]
        last_close = float(df["Close"].iloc[-1])
        return [{
            "ticker": ticker, "metric": "price",
            "period": last_date.strftime("%Y-%m-%d"),
            "period_type": "point",
            "value": last_close, "unit": "USD", "source": "prices",
        }]
