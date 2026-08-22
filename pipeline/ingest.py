# pipeline/ingest.py
import sources                       # triggers auto-discovery
from core.base_source import SOURCES
from core.database import write_facts
from config.universe import get_tickers

def ingest_all():
    tickers = get_tickers()
    for src in SOURCES.values():
        if not src.enabled:
            continue
        for ticker in tickers:
            try:
                write_facts(src.fetch(ticker))
            except Exception as e:
                print(f"[{src.name}] {ticker} failed: {e}")
