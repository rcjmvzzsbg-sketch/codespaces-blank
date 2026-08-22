# core/metrics.py
"""Derivation engine: turns raw EDGAR/Stooq facts into hundreds of metrics."""

# --- Registry -------------------------------------------------------------
DERIVATIONS = {}   # metric_name -> {fn, inputs, category, unit, higher_better}

def derive(name, inputs, category, unit="ratio", higher_better=True):
    """Decorator to register a derived metric."""
    def wrapper(fn):
        DERIVATIONS[name] = {
            "fn": fn, "inputs": inputs, "category": category,
            "unit": unit, "higher_better": higher_better,
        }
        return fn
    return wrapper

def _safe_div(a, b):
    return a / b if (a is not None and b not in (None, 0)) else None

# --- Valuation ------------------------------------------------------------
@derive("pe_ratio", ["price", "eps_ttm"], "valuation", higher_better=False)
def pe_ratio(price, eps_ttm):
    return _safe_div(price, eps_ttm)

@derive("pb_ratio", ["price", "book_value_per_share"], "valuation", higher_better=False)
def pb_ratio(price, bvps):
    return _safe_div(price, bvps)

@derive("fcf_yield", ["free_cash_flow", "market_cap"], "valuation", unit="pct")
def fcf_yield(fcf, mcap):
    r = _safe_div(fcf, mcap)
    return r * 100 if r is not None else None

@derive("ev_ebitda", ["enterprise_value", "ebitda"], "valuation", higher_better=False)
def ev_ebitda(ev, ebitda):
    return _safe_div(ev, ebitda)

# --- Quality / Profitability ---------------------------------------------
@derive("roe", ["net_income", "shareholder_equity"], "quality", unit="pct")
def roe(ni, eq):
    r = _safe_div(ni, eq)
    return r * 100 if r is not None else None

@derive("roic", ["nopat", "invested_capital"], "quality", unit="pct")
def roic(nopat, ic):
    r = _safe_div(nopat, ic)
    return r * 100 if r is not None else None

@derive("gross_margin", ["gross_profit", "revenue"], "quality", unit="pct")
def gross_margin(gp, rev):
    r = _safe_div(gp, rev)
    return r * 100 if r is not None else None

@derive("net_margin", ["net_income", "revenue"], "quality", unit="pct")
def net_margin(ni, rev):
    r = _safe_div(ni, rev)
    return r * 100 if r is not None else None

# --- Leverage / Solvency --------------------------------------------------
@derive("debt_to_equity", ["total_debt", "shareholder_equity"], "leverage", higher_better=False)
def debt_to_equity(debt, eq):
    return _safe_div(debt, eq)

@derive("current_ratio", ["current_assets", "current_liabilities"], "leverage")
def current_ratio(ca, cl):
    return _safe_div(ca, cl)

@derive("interest_coverage", ["ebit", "interest_expense"], "leverage")
def interest_coverage(ebit, interest):
    return _safe_div(ebit, interest)
