# core/macro.py
"""Convenience accessors for the latest macro readings."""

from core.database import get_conn


def latest(series_id: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT value FROM macro WHERE series_id=? ORDER BY date DESC LIMIT 1",
        [series_id],
    ).fetchone()
    conn.close()
    return row[0] if row else None


def regime() -> dict:
    """Snapshot of the current macro environment for scoring context."""
    spread = latest("T10Y2Y")
    return {
        "fed_funds": latest("FEDFUNDS"),
        "ten_year": latest("DGS10"),
        "yield_spread": spread,
        "yield_curve_inverted": (spread is not None and spread < 0),
        "unemployment": latest("UNRATE"),
        "vix": latest("VIXCLS"),
        "cpi": latest("CPIAUCSL"),
    }
