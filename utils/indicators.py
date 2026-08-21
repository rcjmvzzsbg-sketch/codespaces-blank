"""Technical indicator utilities."""
import pandas as pd
import numpy as np


def compute_rsi(series: pd.Series, period: int = 14) -> float:
    """Compute RSI for a price series."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.isna().iloc[-1] else None


def compute_sma(series: pd.Series, period: int) -> float:
    """Compute Simple Moving Average."""
    sma = series.rolling(window=period).mean()
    return sma.iloc[-1] if not sma.isna().iloc[-1] else None


def compute_ema(series: pd.Series, period: int) -> float:
    """Compute Exponential Moving Average."""
    ema = series.ewm(span=period, adjust=False).mean()
    return ema.iloc[-1] if not ema.isna().iloc[-1] else None


def compute_atr(df: pd.DataFrame, period: int = 14) -> float:
    """Compute Average True Range."""
    if len(df) < period:
        return None
    
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    
    tr = pd.concat([
        high - low,
        abs(high - close.shift()),
        abs(low - close.shift())
    ], axis=1).max(axis=1)
    
    atr = tr.rolling(window=period).mean()
    return atr.iloc[-1] if not atr.isna().iloc[-1] else None