# screener/ranker.py
"""Composite scoring: percentile-rank each metric across the universe,
weight into pillar scores, then a final 0-100 grade per stock."""

from core.database import get_conn, write_facts
from config.universe import get_tickers

# metric -> (pillar, higher_is_better)
SCORING_METRICS = {
    # Value (lower is better)
    "pe_ratio":            ("value", False),
    "pb_ratio":            ("value", False),
    "ev_ebitda":           ("value", False),
    "fcf_yield":           ("value", True),
    "sharpe_ratio":        ("momentum", True),

    "ev_ebitda":           ("value", False),
    # Quality (higher is better)
    "roe":                 ("quality", True),
    "piotroski_f":         ("quality", True),
    "altman_z":            ("health", True),

    "net_margin":          ("quality", True),
    "gross_margin":        ("quality", True),
    # Growth (higher is better)
    "revenue_cagr_5y":     ("growth", True),
    "net_income_cagr_5y":  ("growth", True),
    "eps_diluted_cagr_3y": ("growth", True),
    "revenue_growth_yoy":  ("growth", True),
    # Momentum (higher is better)
    "rsi_14":              ("momentum", True),
    "insider_sentiment":   ("momentum", True),
    "price_vs_sma200":     ("momentum", True),
    "roc_60":              ("momentum", True),
    # Health
    "current_ratio":       ("health", True),
    "debt_to_equity":      ("health", False),
}

PILLAR_WEIGHTS = {
    "value": 0.25, "quality": 0.25, "growth": 0.25,
    "momentum": 0.15, "health": 0.10,
}


def _latest_values(metric: str) -> dict:
    """{ticker: value} latest value of a metric across the universe."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT ticker, value FROM facts
           WHERE metric=? AND period=(
               SELECT MAX(period) FROM facts f2
               WHERE f2.ticker=facts.ticker AND f2.metric=facts.metric)
        """, [metric]).fetchall()
    conn.close()
    return {t: v for t, v in rows if v is not None}


def _percentile_rank(values: dict, higher_better: bool) -> dict:
    """Convert {ticker: value} -> {ticker: 0-100 percentile score}."""
    if not values:
        return {}
    items = sorted(values.items(), key=lambda x: x[1], reverse=not higher_better)
    n = len(items)
    scores = {}
    for i, (ticker, _) in enumerate(items):
        # rank 0 (worst) -> 0 ; rank n-1 (best) -> 100
        scores[ticker] = round(i / (n - 1) * 100, 1) if n > 1 else 50.0
    return scores


def compute_scores() -> dict:
    tickers = get_tickers()
    # pillar_scores[ticker][pillar] = list of metric percentile scores
    pillar_scores = {t: {p: [] for p in PILLAR_WEIGHTS} for t in tickers}

    for metric, (pillar, higher_better) in SCORING_METRICS.items():
        values = _latest_values(metric)
        ranks = _percentile_rank(values, higher_better)
        for ticker, score in ranks.items():
            if ticker in pillar_scores:
                pillar_scores[ticker][pillar].append(score)

    results = {}
    facts = []
    for ticker in tickers:
        pillar_avgs = {}
        for pillar, scores in pillar_scores[ticker].items():
            pillar_avgs[pillar] = sum(scores) / len(scores) if scores else 50.0
        composite = sum(pillar_avgs[p] * w for p, w in PILLAR_WEIGHTS.items())
        results[ticker] = {"composite": round(composite, 1), **pillar_avgs}

        # Persist scores as facts (period_type='score')
        for name, val in {"composite_score": composite, **{f"{p}_score": pillar_avgs[p] for p in PILLAR_WEIGHTS}}.items():
            facts.append({
                "ticker": ticker, "metric": name,
                "period": "2026-08-24", "period_type": "score",
                "value": round(val, 1), "unit": "score", "source": "scoring",
            })
    write_facts(facts)
    return results


def print_rankings():
    results = compute_scores()
    ranked = sorted(results.items(), key=lambda x: x[1]["composite"], reverse=True)
    print(f"\n{'RANK':<5}{'TICKER':<8}{'COMPOSITE':<11}{'VALUE':<8}{'QUALITY':<9}{'GROWTH':<8}{'MOMENTUM':<10}{'HEALTH':<8}")
    print("=" * 70)
    for rank, (ticker, s) in enumerate(ranked, 1):
        print(f"{rank:<5}{ticker:<8}{s['composite']:<11}{s['value']:<8.0f}{s['quality']:<9.0f}{s['growth']:<8.0f}{s['momentum']:<10.0f}{s['health']:<8.0f}")


if __name__ == "__main__":
    print_rankings()


# --- Macro-aware scoring adjustment ---------------------------------------
def macro_tilt() -> dict:
    """Return pillar weight adjustments based on current macro regime.
    Returns {pillar: multiplier} to nudge the base weights."""
    from core.macro import regime
    r = regime()
    tilt = {"value": 1.0, "quality": 1.0, "growth": 1.0,
            "momentum": 1.0, "health": 1.0}

    # High rates (10Y > 4.5%) -> balance-sheet health matters more
    if r.get("ten_year") and r["ten_year"] > 4.5:
        tilt["health"] *= 1.3
        tilt["value"] *= 1.15  # expensive money -> value matters

    # Inverted curve -> defensive: reward quality + health, punish momentum
    if r.get("yield_curve_inverted"):
        tilt["quality"] *= 1.3
        tilt["health"] *= 1.3
        tilt["momentum"] *= 0.7

    # Low VIX (calm, risk-on) -> momentum & growth get a boost
    if r.get("vix") and r["vix"] < 20:
        tilt["momentum"] *= 1.2
        tilt["growth"] *= 1.15

    # High VIX (fear) -> flight to quality
    if r.get("vix") and r["vix"] > 25:
        tilt["quality"] *= 1.3
        tilt["value"] *= 1.2

    return tilt


def print_rankings_macro():
    """Rankings with macro-adjusted weights."""
    from core.macro import regime
    r = regime()
    tilt = macro_tilt()

    # Apply tilt to base weights, then renormalize to sum=1
    adj = {p: PILLAR_WEIGHTS[p] * tilt[p] for p in PILLAR_WEIGHTS}
    total = sum(adj.values())
    adj = {p: w / total for p, w in adj.items()}

    print("\n🌍 MACRO REGIME:")
    print(f"   10Y: {r['ten_year']}%  |  Curve inverted: {r['yield_curve_inverted']}"
          f"  |  VIX: {r['vix']}")
    print(f"\n   Base weights : " + "  ".join(f"{p}={PILLAR_WEIGHTS[p]:.2f}" for p in PILLAR_WEIGHTS))
    print(f"   Macro-tilted : " + "  ".join(f"{p}={adj[p]:.2f}" for p in adj))

    # Recompute composites with adjusted weights
    results = compute_scores()  # gives pillar averages per ticker
    ranked = []
    for ticker, s in results.items():
        composite = sum(s[p] * adj[p] for p in PILLAR_WEIGHTS)
        ranked.append((ticker, composite, s))
    ranked.sort(key=lambda x: x[1], reverse=True)

    print(f"\n{'RANK':<5}{'TICKER':<8}{'ADJ SCORE':<11}{'VALUE':<8}{'QUALITY':<9}{'GROWTH':<8}{'MOMENTUM':<10}{'HEALTH':<8}")
    print("=" * 70)
    for rank, (ticker, comp, s) in enumerate(ranked, 1):
        print(f"{rank:<5}{ticker:<8}{comp:<11.1f}{s['value']:<8.0f}{s['quality']:<9.0f}"
              f"{s['growth']:<8.0f}{s['momentum']:<10.0f}{s['health']:<8.0f}")
