# sources/prices.py
"""Historical OHLCV. Primary: yfinance. Fallback: Tiingo (when yfinance
returns empty for a ticker) so a hiccup mid-run doesn't leave gaps."""

import os
import requests
import pandas as pd
import yfinance as yf
from core.base_source import BaseSource, register_source
from core.database import get_conn

TIINGO_KEY = os.environ.get("TIINGO_API_KEY", "")


@register_source
class PriceSource(BaseSource):
    name = "prices"

    # ---------- storage ----------
    def _write_prices(self, ticker: str, df: pd.DataFrame):
        conn = get_conn()
        rows = []
        for idx, r in df.iterrows():
            rows.append((
                ticker, idx.strftime("%Y-%m-%d"),
                float(r["Open"]), float(r["High"]),
                float(r["Low"]), float(r["Close"]),
                int(r["Volume"]) if r["Volume"] == r["Volume"] else 0,
            ))
        conn.executemany(
            """INSERT OR REPLACE INTO prices
               (ticker, date, open, high, low, close, volume)
               VALUES (?, ?, ?, ?, ?, ?, ?)""", rows)
        conn.close()

    # ---------- primary: yfinance ----------
    def _yfinance(self, ticker: str) -> pd.DataFrame:
        try:
            df = yf.download(ticker, period="5y", interval="1d",
                             progress=False, auto_adjust=True)
        except Exception as e:
            print(f"  [prices] yfinance error {ticker}: {e}")
            return pd.DataFrame()
        if df is None or df.empty:
            return pd.DataFrame()
        if hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
            df.columns = df.columns.get_level_values(0)
        return df

    # ---------- fallback: Tiingo ----------
    def _tiingo(self, ticker: str) -> pd.DataFrame:
        if not TIINGO_KEY:
            print(f"  [prices] no TIINGO_API_KEY — cannot fall back for {ticker}")
            return pd.DataFrame()
        url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices"
        params = {"startDate": "2021-01-01", "token": TIINGO_KEY,
                  "format": "json", "resampleFreq": "daily"}
        try:
            r = requests.get(url, params=params,
                             headers={"Content-Type": "application/json"},
                             timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  [prices] Tiingo error {ticker}: {e}")
            return pd.DataFrame()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
        df = df.set_index("date")
        df = df.rename(columns={
            "adjOpen": "Open", "adjHigh": "High", "adjLow": "Low",
            "adjClose": "Close", "adjVolume": "Volume"})
        return df[["Open", "High", "Low", "Close", "Volume"]]

    # ---------- orchestration ----------
    def fetch(self, ticker: str) -> list[dict]:
        source_used = "yfinance"
        df = self._yfinance(ticker)

        if df.empty:                      # yfinance failed -> insurance kicks in
            print(f"  [prices] yfinance empty for {ticker}, trying Tiingo...")
            df = self._tiingo(ticker)
            source_used = "tiingo"

        if df.empty:
            print(f"  [prices] NO DATA for {ticker} (both sources failed)")
            return []

        self._write_prices(ticker, df)
        last_date = df.index[-1]
        last_close = float(df["Close"].iloc[-1])
        print(f"  [prices] {ticker}: {len(df)} bars via {source_used}")
        return [{
            "ticker": ticker, "metric": "price",
            "period": last_date.strftime("%Y-%m-%d"),
            "period_type": "point", "value": last_close,
            "unit": "USD", "source": "prices",
        }]
