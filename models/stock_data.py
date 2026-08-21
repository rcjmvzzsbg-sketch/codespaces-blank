"""Standardized stock data model - all adapters return this structure."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import pandas as pd


@dataclass
class DataPoint:
    """Single metric with metadata."""
    value: float
    timestamp: Optional[datetime] = None
    source: Optional[str] = None
    unit: Optional[str] = None


@dataclass
class StockData:
    """
    Standardized container for all stock data.
    
    This model is returned by ALL adapters regardless of source.
    Your screener logic should work only with this model,
    not with adapter-specific structures.
    """
    # === IDENTIFICATION ===
    ticker: str
    company_name: str
    exchange: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    
    # === REAL-TIME PRICE DATA ===
    current_price: Optional[float] = None
    previous_close: Optional[float] = None
    day_open: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    volume: Optional[int] = None
    avg_volume: Optional[int] = None
    market_cap: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    
    # === FUNDAMENTALS ===
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    beta: Optional[float] = None
    dividend_yield: Optional[float] = None
    dividend_rate: Optional[float] = None
    ex_dividend_date: Optional[datetime] = None
    payout_ratio: Optional[float] = None
    
    # Annual financials
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    stockholders_equity: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    long_term_debt: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    free_cash_flow: Optional[float] = None
    
    # Ratios & Margins
    profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    price_to_book: Optional[float] = None
    price_to_sales: Optional[float] = None
    
    # Growth metrics
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    
    # === HISTORICAL PRICES ===
    price_history: Optional[pd.DataFrame] = None  # Columns: Date, Open, High, Low, Close, Volume, Adj Close
    
    # === TECHNICAL INDICATORS (COMPUTED) ===
    rsi: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    atr: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_lower: Optional[float] = None
    
    # === META ===
    data_source: str = "unknown"
    last_updated: datetime = field(default_factory=datetime.utcnow)
    currency: str = "USD"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        # Remove pandas DataFrame (not JSON serializable)
        result = {k: v for k, v in vars(self).items() 
                  if k != "price_history" and k != "last_updated"}
        result["last_updated"] = self.last_updated.isoformat() if self.last_updated else None
        result["price_history_available"] = self.price_history is not None
        if self.price_history is not None:
            result["price_history_rows"] = len(self.price_history)
        return result
    
    def summary(self) -> str:
        """Human-readable summary."""
        lines = [
            f"=== {self.ticker}: {self.company_name} ===",
            "",
            "PRICE DATA:",
            f"  Current: ${self.current_price or 'N/A':,.2f}" if self.current_price else "  Current: N/A",
            f"  Day Range: ${self.day_low or 'N/A':,.2f} - ${self.day_high or 'N/A':,.2f}" if self.day_low else "  Day Range: N/A",
            f"  Volume: {self.volume:,}" if self.volume else "  Volume: N/A",
            f"  Market Cap: ${self.market_cap:,.0f}" if self.market_cap else "  Market Cap: N/A",
            "",
            "FUNDAMENTALS:",
            f"  P/E Ratio: {self.pe_ratio:.2f}" if self.pe_ratio else "  P/E Ratio: N/A",
            f"  EPS: ${self.eps:.2f}" if self.eps else "  EPS: N/A",
            f"  Beta: {self.beta:.2f}" if self.beta else "  Beta: N/A",
            f"  Dividend Yield: {self.dividend_yield:.2%}" if self.dividend_yield else "  Dividend Yield: N/A",
            "",
            "FINANCIALS:",
            f"  Revenue: ${self.revenue:,.0f}" if self.revenue else "  Revenue: N/A",
            f"  Net Income: ${self.net_income:,.0f}" if self.net_income else "  Net Income: N/A",
            f"  Total Assets: ${self.total_assets:,.0f}" if self.total_assets else "  Total Assets: N/A",
            f"  Debt-to-Equity: {self.debt_to_equity:.2f}" if self.debt_to_equity else "  Debt-to-Equity: N/A",
            "",
            "TECHNICALS:",
            f"  RSI (14): {self.rsi:.1f}" if self.rsi else "  RSI: N/A",
            f"  SMA 50: ${self.sma_50:.2f}" if self.sma_50 else "  SMA 50: N/A",
            f"  SMA 200: ${self.sma_200:.2f}" if self.sma_200 else "  SMA 200: N/A",
            "",
            f"Data Source: {self.data_source}",
            f"Last Updated: {self.last_updated.strftime('%Y-%m-%d %H:%M:%S')}" if self.last_updated else "Last Updated: N/A",
        ]
        return "\n".join(lines)