# STOCK SCREENER — DATA FACTORY SUMMARY
_Handoff reference for the downstream prediction/analysis engine._
_Last built: 2026-08-27_

## PURPOSE
A neutral financial-DATA factory. It ingests, computes, and exports objective
metrics for ~940 US-tradeable stocks. It deliberately contains NO rankings,
NO composite scores, and NO buy/sell opinions — the downstream engine forms
its own independent judgment.

## THE UNIVERSE
- ~940 tickers (US-listed, China-domiciled filers excluded via SEC filter)
- ~1.27M facts | ~188 objective metrics per company (coverage varies by filer)
- Foreign filers (20-F/IFRS) have sparser fundamentals → many metrics = n/a (honest)

## DATA SOURCES (6 ingest plugins, in core/base_source SOURCES registry)
| Source    | Provides                                              | Cadence   |
|-----------|-------------------------------------------------------|-----------|
| edgar     | SEC XBRL fundamentals (income/balance/cashflow, ~2400/co) | Quarterly |
| prices    | yfinance OHLCV daily bars (~1254/co, ~5yr)            | Daily     |
| fred      | Macro series (GDP,CPI,DGS10,DGS2,UNRATE,FEDFUNDS,T10Y2Y,VIX) | Daily |
| finra     | Short interest                                        | Bi-monthly|
| insider   | SEC Form 4 insider transactions                       | Continuous|
| wikidata  | Sector / industry classification                      | Static    |

## METRIC LAYERS (pipeline order)
1. pipeline.derive       — core ratios from raw facts (margins, ROE, P/E, etc.)
2. metrics.technicals    — RSI, SMA, MACD, Bollinger, ATR, ADX, CCI...
3. metrics.technicals2   — extended technicals, volume, momentum (ROC)
4. metrics.growth        — revenue/income/EPS CAGRs (3y,5y), YoY growth
5. metrics.growth2       — extended growth + efficiency (DSO/DIO/DPO/CCC)
6. metrics.scores        — piotroski_f (0-9 financial strength)
7. metrics.risk          — beta, sharpe, volatility, drawdown, annual_return (vs SPY)
8. metrics.ttm           — trailing-twelve-month recomputes (pe_ttm, etc.)
9. metrics.beneish       — beneish_m (earnings-manipulation M-score)
   (also altman_z bankruptcy score computed here/derive)
NOTE: metrics.forensic (composite verdict) and screener/ranker.py (composite_score
+ pillar ranking) are ARCHIVED/EXCLUDED — no ranking exists in outputs.

## OBJECTIVE SCORE METRICS KEPT (they are standard formulas, not our opinion)
- piotroski_f : 0-9, higher = financially stronger
- altman_z    : bankruptcy distress (>2.99 safe, <1.81 distress)
- beneish_m   : > -1.78 flags possible earnings manipulation
  (Caution: hypergrowth firms trigger false positives — e.g. NVDA. It's a
   screening flag to investigate, not a verdict.)

## OUTPUT (where the engine pulls data) — folder: output/
- output/universe_data.json  — {ticker: {metric: value}} ALL tickers (load once)
- output/universe_data.csv   — flat table, ticker rows × ~191 metric columns
- output/data/{TICKER}.json  — per-stock detail {ticker, metrics:{...}}
All outputs use each metric's LATEST available period. No rankings included.

## DATABASE
- DuckDB file: screener.duckdb
- Table: facts (ticker, metric, period, period_type, value, unit, source)
- core/database.py : init_db(), get_conn(), write_facts()

## HOW TO REFRESH
- python -m pipeline.run_daily        (prices, technicals, risk, TTM — fast ~15m)
- python -m pipeline.run_fundamental  (edgar + fundamentals + growth — weekly)
- python -m pipeline.export           (regenerate output/ files)
Automated nightly/weekly via GitHub Actions (.github/workflows/).

## KNOWN NOTES
- ~6 tickers were lock-victims during ingest, backfilled successfully.
- Beneish/Altman/Piotroski have lower coverage (need full financials);
  price-based metrics cover ~920-940 tickers.
