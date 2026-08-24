# app/app.py
"""Streamlit dashboard for the stock screener."""

import streamlit as st
import pandas as pd
from core.database import get_conn

st.set_page_config(page_title="Stock Screener", layout="wide")
st.title("📊 Multi-Factor Stock Screener")


@st.cache_data(ttl=300)
def load_scores():
    conn = get_conn()
    df = conn.execute("""
        SELECT ticker, metric, value FROM facts
        WHERE period_type='score'
    """).fetchdf()
    conn.close()
    if df.empty:
        return pd.DataFrame()
    # Pivot: one row per ticker, one column per score
    return df.pivot(index="ticker", columns="metric", values="value").reset_index()


@st.cache_data(ttl=300)
def load_metric(metric):
    conn = get_conn()
    df = conn.execute("""
        SELECT ticker, value FROM facts
        WHERE metric=? AND period=(
            SELECT MAX(period) FROM facts f2
            WHERE f2.ticker=facts.ticker AND f2.metric=facts.metric)
    """, [metric]).fetchdf()
    conn.close()
    return dict(zip(df["ticker"], df["value"])) if not df.empty else {}


scores = load_scores()

if scores.empty:
    st.warning("No scores found. Run `python -m screener.ranker` first.")
    st.stop()

# ---- Sidebar filters ----
st.sidebar.header("🔎 Filters")
min_composite = st.sidebar.slider("Min Composite Score", 0, 100, 0)
sort_col = st.sidebar.selectbox(
    "Sort by",
    ["composite_score", "value_score", "quality_score",
     "growth_score", "momentum_score", "health_score"],
)

# ---- Main leaderboard ----
st.subheader("🏆 Rankings")
cols = ["ticker", "composite_score", "value_score", "quality_score",
        "growth_score", "momentum_score", "health_score"]
view = scores[[c for c in cols if c in scores.columns]].copy()
view = view[view["composite_score"] >= min_composite]
view = view.sort_values(sort_col, ascending=False).reset_index(drop=True)
view.index += 1  # rank starts at 1

st.dataframe(
    view.style.background_gradient(
        subset=[c for c in view.columns if c.endswith("_score")],
        cmap="RdYlGn", vmin=0, vmax=100,
    ).format({c: "{:.0f}" for c in view.columns if c.endswith("_score")}),
    use_container_width=True,
)

# ---- Drill-down ----
st.subheader("🔬 Company Detail")
pick = st.selectbox("Select a company", view["ticker"].tolist())

c1, c2, c3 = st.columns(3)
raw_metrics = {
    "Valuation": ["price", "market_cap", "pe_ratio", "pb_ratio"],
    "Quality": ["roe", "net_margin", "gross_margin"],
    "Growth": ["revenue_cagr_5y", "net_income_cagr_5y", "revenue_growth_yoy"],
}
for col, (label, mlist) in zip([c1, c2, c3], raw_metrics.items()):
    with col:
        st.markdown(f"**{label}**")
        for m in mlist:
            val = load_metric(m).get(pick)
            if val is not None:
                st.metric(m, f"{val:,.2f}")

# ---- Price chart ----
st.subheader("📈 Price History")
conn = get_conn()
pdf = conn.execute(
    "SELECT date, close FROM prices WHERE ticker=? ORDER BY date", [pick]
).fetchdf()
conn.close()
if not pdf.empty:
    st.line_chart(pdf.set_index("date")["close"])
