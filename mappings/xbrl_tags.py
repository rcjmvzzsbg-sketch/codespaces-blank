# mappings/xbrl_tags.py
"""Maps clean metric names -> list of candidate SEC XBRL tags.
Companies use different tags over time, so we try each in priority order."""

XBRL_MAP = {
    # --- Income Statement ---
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ],
    "cost_of_revenue": ["CostOfRevenue", "CostOfGoodsAndServicesSold"],
    "gross_profit": ["GrossProfit"],
    "operating_income": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "interest_expense": ["InterestExpense", "InterestExpenseDebt"],
    "eps_basic": ["EarningsPerShareBasic"],
    "eps_diluted": ["EarningsPerShareDiluted"],

    # --- Balance Sheet ---
    "total_assets": ["Assets"],
    "current_assets": ["AssetsCurrent"],
    "total_liabilities": ["Liabilities"],
    "current_liabilities": ["LiabilitiesCurrent"],
    "shareholder_equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "total_debt": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue"],
    "shares_outstanding": ["CommonStockSharesOutstanding"],

    # --- Cash Flow ---
    "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
}
