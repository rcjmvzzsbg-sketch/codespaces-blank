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


# --- Intermediates (derived from raw, feed other derivations) -------------
@derive("ebit", ["operating_income"], "intermediate", unit="USD")
def ebit(operating_income):
    return operating_income  # operating income ≈ EBIT for most companies

@derive("free_cash_flow", ["operating_cash_flow", "capex"], "intermediate", unit="USD")
def free_cash_flow(ocf, capex):
    if ocf is None or capex is None:
        return None
    return ocf - capex


# --- Price-based intermediates (need Stooq/yfinance price + EDGAR shares) --
@derive("market_cap", ["price", "shares_outstanding"], "valuation", unit="USD")
def market_cap(price, shares):
    if price is None or shares is None:
        return None
    return price * shares

@derive("book_value_per_share", ["shareholder_equity", "shares_outstanding"], "valuation", unit="USD")
def book_value_per_share(equity, shares):
    if equity is None or shares in (None, 0):
        return None
    return equity / shares

@derive("eps_ttm", ["eps_diluted"], "valuation", unit="USD")
def eps_ttm(eps_diluted):
    return eps_diluted  # using latest annual diluted EPS as a stand-in for now


# --- Expanded ratios (use newly-mapped line items) ------------------------
@derive("rd_intensity", ["rd_expense", "revenue"], "quality", unit="pct")
def rd_intensity(rd, rev):
    r = _safe_div(rd, rev)
    return r * 100 if r is not None else None

@derive("operating_margin", ["operating_income", "revenue"], "quality", unit="pct")
def operating_margin(oi, rev):
    r = _safe_div(oi, rev)
    return r * 100 if r is not None else None

@derive("roa", ["net_income", "total_assets"], "quality", unit="pct")
def roa(ni, assets):
    r = _safe_div(ni, assets)
    return r * 100 if r is not None else None

@derive("asset_turnover", ["revenue", "total_assets"], "quality")
def asset_turnover(rev, assets):
    return _safe_div(rev, assets)

@derive("quick_ratio", ["current_assets", "inventory", "current_liabilities"], "leverage")
def quick_ratio(ca, inv, cl):
    if ca is None or cl in (None, 0):
        return None
    inv = inv or 0
    return (ca - inv) / cl

@derive("cash_ratio", ["cash", "current_liabilities"], "leverage")
def cash_ratio(cash, cl):
    return _safe_div(cash, cl)

@derive("goodwill_to_assets", ["goodwill", "total_assets"], "quality", unit="pct", higher_better=False)
def goodwill_to_assets(gw, assets):
    r = _safe_div(gw, assets)
    return r * 100 if r is not None else None

@derive("effective_tax_rate", ["income_tax", "pretax_income"], "quality", unit="pct", higher_better=False)
def effective_tax_rate(tax, pretax):
    r = _safe_div(tax, pretax)
    return r * 100 if r is not None else None

@derive("fcf_margin", ["free_cash_flow", "revenue"], "quality", unit="pct")
def fcf_margin(fcf, rev):
    r = _safe_div(fcf, rev)
    return r * 100 if r is not None else None

@derive("buyback_yield", ["stock_buybacks", "market_cap"], "value", unit="pct")
def buyback_yield(bb, mcap):
    r = _safe_div(bb, mcap)
    return r * 100 if r is not None else None

@derive("dividend_yield", ["dividends_paid", "market_cap"], "value", unit="pct")
def dividend_yield(div, mcap):
    r = _safe_div(div, mcap)
    return r * 100 if r is not None else None

@derive("ebitda", ["operating_income", "depreciation_amortization"], "intermediate", unit="USD")
def ebitda(oi, da):
    if oi is None:
        return None
    return oi + (da or 0)
