# metrics/technicals2.py
"""Advanced technical indicators: Stochastic, Williams %R, OBV, CCI, MFI, ADX.
Pure computation on stored OHLCV — extends the base technicals module."""

import numpy as np
import pandas as pd
from core.database import get_conn, write_facts
from config.universe import get_tickers


def _ohlcv(ticker):
    conn = get_conn()
    df = conn.execute(
        "SELECT date, open, high, low, close, volume FROM prices WHERE ticker=? ORDER BY date",
        [ticker]).fetchdf()
    conn.close()
    return df


def compute_indicators(ticker):
    df = _ohlcv(ticker)
    if len(df) < 60:
        return []
    high, low, close, vol = df["high"], df["low"], df["close"], df["volume"]
    out = {}

    # --- Stochastic Oscillator (%K, 14) ---
    ll = low.rolling(14).min()
    hh = high.rolling(14).max()
    k = 100 * (close - ll) / (hh - ll)
    out["stochastic_k"] = float(k.iloc[-1])
    out["stochastic_d"] = float(k.rolling(3).mean().iloc[-1])  # %D = 3-SMA of %K

    # --- Williams %R (14) ---
    out["williams_r"] = float(-100 * (hh.iloc[-1] - close.iloc[-1]) / (hh.iloc[-1] - ll.iloc[-1]))

    # --- On-Balance Volume (OBV) ---
    direction = np.sign(close.diff()).fillna(0)
    obv = (direction * vol).cumsum()
    out["obv"] = float(obv.iloc[-1])

    # --- Commodity Channel Index (CCI, 20) ---
    tp = (high + low + close) / 3
    sma_tp = tp.rolling(20).mean()
    mad = tp.rolling(20).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    cci = (tp - sma_tp) / (0.015 * mad)
    out["cci_20"] = float(cci.iloc[-1])

    # --- Money Flow Index (MFI, 14) ---
    raw_mf = tp * vol
    pos_mf = raw_mf.where(tp > tp.shift(1), 0).rolling(14).sum()
    neg_mf = raw_mf.where(tp < tp.shift(1), 0).rolling(14).sum()
    mfi = 100 - (100 / (1 + pos_mf / neg_mf.replace(0, np.nan)))
    out["mfi_14"] = float(mfi.iloc[-1])

    # --- Average Directional Index (ADX, 14) ---
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
    tr = pd.concat([high - low, (high - close.shift()).abs(),
                    (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(14).mean() / atr)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    out["adx_14"] = float(dx.rolling(14).mean().iloc[-1])

    facts = []
    for metric, value in out.items():
        if value is not None and not (isinstance(value, float) and np.isnan(value)):
            facts.append({
                "ticker": ticker, "metric": metric, "period": "2026-08-24",
                "period_type": "point", "value": round(value, 4),
                "unit": "indicator", "source": "technical",
            })
    return facts


def compute_all():
    total = 0
    for ticker in get_tickers():
        facts = compute_indicators(ticker)
        write_facts(facts)
        total += len(facts)
        print(f"  {ticker:<6} {len(facts):>3} advanced indicators")
    print(f"\n✅ Advanced technicals complete: {total} facts.")
    return total


if __name__ == "__main__":
    compute_all()
