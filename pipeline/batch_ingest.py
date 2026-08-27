# pipeline/batch_ingest.py
"""Resilient batch ingest over the full universe: throttled, checkpointed,
resumable. If it dies at ticker #600, rerun and it skips the done ones."""

import os, time, json
import sources                       # triggers auto-discovery of all plugins
from core.base_source import SOURCES
from core.database import write_facts
from config.universe import get_tickers

CHECKPOINT = "config/ingest_checkpoint.json"
FAILLOG = "config/ingest_failures.json"
SEC_SLEEP = 0.12      # ~8 req/sec, under SEC's 10/sec limit


def _load_json(path, default):
    if os.path.exists(path):
        try: return json.load(open(path))
        except Exception: return default
    return default


def run(resume=True):
    done = set(_load_json(CHECKPOINT, []))
    failures = _load_json(FAILLOG, {})
    if not resume:
        done, failures = set(), {}

    tickers = get_tickers()
    active = [s for s in SOURCES.values() if getattr(s, "enabled", True)]
    print(f"🚀 Batch ingest: {len(tickers)} tickers, {len(active)} sources")
    print(f"   Sources: {[s.name for s in active]}")
    print(f"   Resuming: {len(done)} done, {len(tickers)-len(done)} remaining\n")

    for i, ticker in enumerate(tickers, 1):
        if ticker in done:
            continue
        t0, total = time.time(), 0
        for src in active:
            try:
                rows = src.fetch(ticker)
                write_facts(rows or [])
                total += len(rows or [])
                if src.name in ("edgar", "prices"):
                    time.sleep(SEC_SLEEP)
            except Exception as e:
                failures.setdefault(ticker, []).append(f"{src.name}: {e}")
        done.add(ticker)
        json.dump(sorted(done), open(CHECKPOINT, "w"))
        json.dump(failures, open(FAILLOG, "w"), indent=2)
        flag = " ⚠️" if ticker in failures else ""
        print(f"  [{i:>3}/{len(tickers)}] ✓ {ticker:<6} {total:>5} facts  ({time.time()-t0:.1f}s){flag}")

    print(f"\n✅ Ingest done: {len(done)}/{len(tickers)} processed, {len(failures)} had partial failures")
    if failures:
        print(f"   Failure log: {FAILLOG}")


if __name__ == "__main__":
    import sys
    run(resume="--fresh" not in sys.argv)
