# metrics/forensic.py
"""Combined forensic verdict: reads Piotroski + Altman + Beneish together.
A Beneish flag is only a TRUE concern when paired with financial distress
(low Altman Z). High-growth firms trip Beneish but stay clean via strong Z."""

from core.database import get_conn, write_facts
from config.universe import get_tickers


def verdict(ticker):
    conn = get_conn()
    def g(m):
        r = conn.execute("SELECT value FROM facts WHERE ticker=? AND metric=?",
                         [ticker, m]).fetchone()
        return r[0] if r else None
    f, z, m = g("piotroski_f"), g("altman_z"), g("beneish_m")
    conn.close()

    if None in (z, m):
        return None, "insufficient data"

    beneish_flag = m > -1.78
    distress = z < 1.81

    if beneish_flag and distress:
        v, label = 0, "🚨 RED FLAG (manipulation pattern + distress)"
    elif beneish_flag and not distress:
        v, label = 2, "⚠️ growth false-positive (Beneish tripped, Z strong)"
    elif not beneish_flag and distress:
        v, label = 1, "⚠️ distressed but no manipulation pattern"
    else:
        v, label = 3, "✅ clean (honest + solvent)"

    # bonus point for strong Piotroski
    if f is not None and f >= 7 and v >= 2:
        v = min(v + 1, 4)
    return v, label


def compute_all():
    total = 0
    print(f"{'TICKER':<8}{'VERDICT'}")
    print("=" * 60)
    for ticker in get_tickers():
        v, label = verdict(ticker)
        if v is None:
            print(f"{ticker:<8}{label}")
            continue
        write_facts([{
            "ticker": ticker, "metric": "forensic_score", "period": "2026-08-24",
            "period_type": "score", "value": float(v),
            "unit": "score", "source": "scores",
        }])
        total += 1
        print(f"{ticker:<8}{label}")
    print(f"\n✅ Forensic verdict complete: {total} facts.")
    return total


if __name__ == "__main__":
    compute_all()
