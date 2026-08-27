"""FUNDAMENTAL tier: slow, filing-driven. Runs weekly (Sunday)."""
import subprocess, sys
STEPS = ["pipeline.batch_ingest","pipeline.derive","metrics.technicals",
         "metrics.technicals2","metrics.growth","metrics.growth2",
         "metrics.scores","metrics.risk","metrics.ttm","metrics.beneish",
         "pipeline.export"]
def main():
    for m in STEPS:
        print(f"▶ {m}"); r=subprocess.run([sys.executable,"-m",m])
        if r.returncode!=0: sys.exit(f"❌ {m} failed (exit {r.returncode})")
    print("✅ Fundamental run complete")
if __name__=="__main__": main()
