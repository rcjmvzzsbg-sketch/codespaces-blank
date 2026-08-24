# metrics/technicals.py
"""Technical indicators computed from the prices table.
Reads OHLCV history -> writes technical facts (period_type='point')."""

import pandas as pd
from core.database import get_conn, write_facts
from config.universe import get_tickers


def _load_prices(ticker: str) -> pd.DataFrame:
    conn = get_conn()
    df = conn.execute(
        """SELECT date, open, high, low, close, volume
           FROM prices WHERE ticker=? ORDER BY date""",
        [ticker],
    ).fetchdf()
    conn.close()
    return df


def _rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return float((100 - 100 / (1 + rs)).iloc[-1])


def _atr(df: pd.DataFrame, period: int = 14) -> float:
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return float(tr.rolling(period).mean().iloc[-1])


def compute_technicals(ticker: str) -> list[dict]:
    df = _load_prices(ticker)
    if len(df) < 200:
        return []  # need enough history for 200-day SMA

    close = df["close"]
    last_date = str(df["date"].iloc[-1])
    price = float(close.iloc[-1])
    out = {}

    # --- Trend: moving averages ---
    for p in (20, 50, 200):
        out[f"sma_{p}"] = float(close.rolling(p).mean().iloc[-1])
        out[f"ema_{p}"] = float(close.ewm(span=p).mean().iloc[-1])
    out["price_vs_sma50"] = (price / out["sma_50"] - 1) * 100
    out["price_vs_sma200"] = (price / out["sma_200"] - 1) * 100
    # Golden/death cross signal (1 = bullish, 0 = bearish)
    out["golden_cross"] = 1.0 if out["sma_50"] > out["sma_200"] else 0.0

    # --- Momentum: RSI ---
    out["rsi_14"] = _rsi(close, 14)

    # --- Momentum: MACD (12/26/9) ---
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    out["macd"] = float(macd.iloc[-1])
    out["macd_signal"] = float(signal.iloc[-1])
    out["macd_hist"] = float((macd - signal).iloc[-1])

    # --- Momentum: rate of change ---
    out["roc_20"] = (price / float(close.iloc[-21]) - 1) * 100 if len(close) > 21 else None
    out["roc_60"] = (price / float(close.iloc[-61]) - 1) * 100 if len(close) > 61 else None

    # --- Volatility: ATR + Bollinger position ---
    out["atr_14"] = _atr(df, 14)
    sma20 = close.rolling(20).mean().iloc[-1]
    std20 = close.rolling(20).std().iloc[-1]
    if std20:
        out["bollinger_pct"] = float((price - (sma20 - 2 * std20)) / (4 * std20) * 100)

    # --- 52-week range ---
    window = close.tail(252)
    hi52, lo52 = float(window.max()), float(window.min())
    out["high_52w"] = hi52
    out["low_52w"] = lo52
    out["pct_from_52w_high"] = (price / hi52 - 1) * 100
    out["pct_from_52w_low"] = (price / lo52 - 1) * 100

    # --- Volume ---
    out["avg_volume_20"] = float(df["volume"].tail(20).mean())
    out["avg_volume_50"] = float(df["volume"].tail(50).mean())

    # Package as facts
    facts = []
    for metric, value in out.items():
        if value is None:
            continue
        facts.append({
            "ticker": ticker, "metric": metric,
            "period": last_date, "period_type": "point",
            "value": float(value), "unit": "ratio", "source": "technical",
        })
    return facts


def compute_all() -> int:
    total = 0
    for ticker in get_tickers():
        facts = compute_technicals(ticker)
        write_facts(facts)
        total += len(facts)
        print(f"  {ticker:<6} {len(facts):>3} technical indicators")
    print(f"\n✅ Technicals complete: {total} indicators computed.")
    return total


if __name__ == "__main__":
    compute_all()
