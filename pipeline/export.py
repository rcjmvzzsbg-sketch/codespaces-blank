# pipeline/export.py
"""Export the RAW METRIC data (no rankings, no composite score) for an
independent analysis engine to consume. Deliberately excludes this
project's own scoring so the downstream engine forms its own judgment."""

import os, json
from core.database import get_conn

OUT = "output"
DATA = f"{OUT}/data"

# Rankings/opinions we EXCLUDE so the analysis engine isn't anchored:
EXCLUDE = {"composite_score", "value", "quality", "growth_score",
           "momentum", "health", "forensic_score"}
# NOTE: we keep the raw forensic *components* (piotroski_f, altman_z,
# beneish_m) because those are objective data, not our verdict. But we
# drop 'forensic_score' since that's our composite judgment. Adjust to taste.


def _latest_all():
    conn = get_conn()
    rows = conn.execute("""
        SELECT ticker, metric, value FROM facts f
        WHERE period = (SELECT MAX(period) FROM facts f2
                        WHERE f2.ticker=f.ticker AND f2.metric=f.metric)
    """).fetchall()
    conn.close()
    data = {}
    for t, m, v in rows:
        if m in EXCLUDE:
            continue
        data.setdefault(t, {})[m] = v
    return data


def export():
    os.makedirs(DATA, exist_ok=True)
    data = _latest_all()
    print(f"Exporting {len(data)} tickers (rankings EXCLUDED)...")

    # per-ticker JSON — pure data, no opinion
    for t, metrics in data.items():
        with open(f"{DATA}/{t}.json", "w") as f:
            json.dump({"ticker": t, "metrics": metrics}, f, indent=2, default=str)

    # a single combined dataset file too (convenient for the engine to load once)
    with open(f"{OUT}/universe_data.json", "w") as f:
        json.dump(data, f, indent=2, default=str)

    # flat CSV of all metrics (no rank, alphabetical by ticker) for pandas
    import csv
    all_metrics = sorted({m for mm in data.values() for m in mm})
    with open(f"{OUT}/universe_data.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker"] + all_metrics)
        for t in sorted(data):
            w.writerow([t] + [data[t].get(m, "") for m in all_metrics])

    print(f"✅ {len(data)} per-ticker JSONs in {DATA}/")
    print(f"✅ output/universe_data.json (combined)")
    print(f"✅ output/universe_data.csv ({len(all_metrics)} metric columns)")
    print(f"   Excluded ranking metrics: {sorted(EXCLUDE)}")


if __name__ == "__main__":
    export()
