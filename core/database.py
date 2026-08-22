import duckdb
from datetime import datetime
from pathlib import Path

DB_PATH = "screener.duckdb"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

def get_conn():
    return duckdb.connect(DB_PATH)

def init_db():
    conn = get_conn()
    conn.execute(SCHEMA_PATH.read_text())
    conn.close()

def write_facts(rows: list[dict]):
    if not rows:
        return
    conn = get_conn()
    ts = datetime.utcnow()
    conn.executemany(
        """INSERT OR REPLACE INTO facts
           (ticker, metric, period, period_type, value, unit, source, ingested_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        [(r["ticker"], r["metric"], r["period"], r["period_type"],
          r.get("value"), r.get("unit"), r.get("source"), ts) for r in rows],
    )
    conn.close()

def get_fact(ticker: str, metric: str, period_type: str = "ttm"):
    conn = get_conn()
    row = conn.execute(
        """SELECT value FROM facts
           WHERE ticker=? AND metric=? AND period_type=?
           ORDER BY period DESC LIMIT 1""",
        [ticker, metric, period_type],
    ).fetchone()
    conn.close()
    return row[0] if row else None
