# mappings/xbrl_tags.py
"""Clean metric name -> candidate SEC XBRL tags (tried in priority order)."""

XBRL_MAP = {
    # ---------- Income Statement ----------
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues", "SalesRevenueNet",
    ],
    "cost_of_revenue": ["CostOfRevenue", "CostOfGoodsAndServicesSold"],
    "gross_profit": ["GrossProfit"],
    "rd_expense": ["ResearchAndDevelopmentExpense"],
    "sga_expense": ["SellingGeneralAndAdministrativeExpense"],
    "operating_expenses": ["OperatingExpenses", "CostsAndExpenses"],
    "operating_income": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "pretax_income": ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"],
    "income_tax": ["IncomeTaxExpenseBenefit"],
    "interest_expense": ["InterestExpense", "InterestExpenseDebt"],
    "depreciation_amortization": ["DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet"],
    "eps_basic": ["EarningsPerShareBasic"],
    "eps_diluted": ["EarningsPerShareDiluted"],

    # ---------- Balance Sheet: Assets ----------
    "total_assets": ["Assets"],
    "current_assets": ["AssetsCurrent"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue"],
    "short_term_investments": ["ShortTermInvestments"],
    "receivables": ["AccountsReceivableNetCurrent"],
    "inventory": ["InventoryNet"],
    "ppe_net": ["PropertyPlantAndEquipmentNet"],
    "goodwill": ["Goodwill"],
    "intangibles": ["IntangibleAssetsNetExcludingGoodwill", "FiniteLivedIntangibleAssetsNet"],

    # ---------- Balance Sheet: Liabilities & Equity ----------
    "total_liabilities": ["Liabilities"],
    "current_liabilities": ["LiabilitiesCurrent"],
    "accounts_payable": ["AccountsPayableCurrent"],
    "long_term_debt": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "total_debt": ["DebtLongtermAndShorttermCombinedAmount", "LongTermDebt"],
    "deferred_revenue": ["ContractWithCustomerLiabilityCurrent", "DeferredRevenueCurrent"],
    "shareholder_equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "retained_earnings": ["RetainedEarningsAccumulatedDeficit"],
    "shares_outstanding": ["CommonStockSharesOutstanding"],

    # ---------- Cash Flow ----------
    "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "investing_cash_flow": ["NetCashProvidedByUsedInInvestingActivities"],
    "financing_cash_flow": ["NetCashProvidedByUsedInFinancingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    "dividends_paid": ["PaymentsOfDividendsCommonStock", "PaymentsOfDividends"],
    "stock_buybacks": ["PaymentsForRepurchaseOfCommonStock"],
    "stock_based_comp": ["ShareBasedCompensation"],
}

# --- Separate depreciation/amortization (MSFT, GOOGL report these split) ---
XBRL_MAP["depreciation"] = ["Depreciation"]
XBRL_MAP["amortization"] = ["AmortizationOfIntangibleAssets"]
XBRL_MAP["depreciation_amortization"].append("DepreciationAndAmortization")
