"""DAILY tier: fast, price-driven refresh. Runs weekday mornings."""
import subprocess, sys
STEPS = ["pipeline.derive","metrics.technicals","metrics.technicals2",
         "metrics.risk","metrics.ttm","pipeline.export"]
def main():
    for m in STEPS:
        print(f"▶ {m}"); r=subprocess.run([sys.executable,"-m",m])
        if r.returncode!=0: sys.exit(f"❌ {m} failed (exit {r.returncode})")
    print("✅ Daily run complete")
if __name__=="__main__": main()
