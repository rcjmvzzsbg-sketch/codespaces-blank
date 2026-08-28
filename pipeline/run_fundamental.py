"""FUNDAMENTAL tier: slow, filing-driven. Full rebuild from scratch.
Runs weekly. Clears checkpoint so the cloud (which has no persisted DB)
always does a complete ingest."""
import subprocess, sys, os
from core.database import init_db

def main():
    # fresh start: remove stale checkpoint, ensure facts table exists
    for f in ["config/ingest_checkpoint.json", "config/ingest_failures.json"]:
        if os.path.exists(f):
            os.remove(f); print(f"🧹 cleared {f}")
    init_db()  # create facts table if missing
    print("✅ DB initialized")

    STEPS = ["pipeline.batch_ingest","pipeline.derive","metrics.technicals",
             "metrics.technicals2","metrics.growth","metrics.growth2",
             "metrics.scores","metrics.risk","metrics.ttm","metrics.beneish",
             "pipeline.export"]
    for m in STEPS:
        print(f"▶ {m}"); r=subprocess.run([sys.executable,"-m",m])
        if r.returncode!=0: sys.exit(f"❌ {m} failed (exit {r.returncode})")
    print("✅ Fundamental run complete")

if __name__=="__main__": main()
