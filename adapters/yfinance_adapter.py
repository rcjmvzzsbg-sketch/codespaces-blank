"""Adapter for Yahoo Finance via yfinance library."""
import logging
from datetime import datetime
from typing import Optional
import yfinance as yf
import pandas as pd

from .base import DataAdapter
from ..models.stock_data import StockData

logger = logging.getLogger(__name__)


class YFinanceAdapter(DataAdapter):
    """
    Adapter for Yahoo Finance data via yfinance library.
    
    NOTE: This is a PROTOTYPE adapter. It will be replaced
    by SEC EDGAR and Stooq in later phases when yfinance breaks.
    """
    
    @property
    def name(self) -> str:
        return "yfinance (Yahoo Finance)"
    
    @property
    def supports(self) -> list:
        return ["price", "fundamentals", "history", "metadata", "technicals"]
    
    def fetch(self, ticker: str, period: str = "1y", **kwargs) -> Optional[StockData]:
        """Fetch all data for ticker from yfinance."""
        if not self.validate_ticker(ticker):
            logger.warning(f"Invalid ticker format: {ticker}")
            return None
        
        try:
            # Initialize Ticker object
            stock = yf.Ticker(ticker)
            
            # Get info (fundamentals + metadata)
            info = stock.info
            
            # Get historical data
            history = stock.history(period=period)
            
            # Compute technical indicators
            tech = self._compute_technicals(history)
            
            # Build StockData object
            data = StockData(
                # Identification
                ticker=ticker.upper(),
                company_name=info.get("shortName") or info.get("longName") or ticker.upper(),
                exchange=info.get("exchange") or "N/A",
                sector=info.get("sector"),
                industry=info.get("industry"),
                website=info.get("website"),
                description=info.get("longBusinessSummary"),
                
                # Real-time price data
                current_price=info.get("regularMarketPrice"),
                previous_close=info.get("previousClose"),
                day_open=info.get("open"),
                day_high=info.get("dayHigh"),
                day_low=info.get("dayLow"),
                volume=info.get("volume"),
                avg_volume=info.get("averageVolume"),
                market_cap=info.get("marketCap"),
                bid=info.get("bid"),
                ask=info.get("ask"),
                
                # Fundamentals
                pe_ratio=info.get("trailingPE") or info.get("forwardPE"),
                eps=info.get("trailingEps") or info.get("forwardEps"),
                beta=info.get("beta"),
                dividend_yield=info.get("dividendYield"),
                dividend_rate=info.get("dividendRate"),
                ex_dividend_date=self._parse_date(info.get("exDividendDate")),
                payout_ratio=info.get("payoutRatio"),
                
                # Annual financials (from balance sheet & income statement)
                revenue=info.get("totalRevenue"),
                net_income=info.get("netIncomeToCommon") or self._extract_financial(stock, "netIncome"),
                gross_profit=self._extract_financial(stock, "grossProfits"),
                operating_income=self._extract_financial(stock, "operatingIncome"),
                total_assets=self._extract_financial(stock, "totalAssets"),
                total_liabilities=self._extract_financial(stock, "totalLiabilities"),
                stockholders_equity=self._extract_financial(stock, "totalStockholderEquity"),
                cash_and_equivalents=self._extract_financial(stock, "cash"),
                long_term_debt=self._extract_financial(stock, "longTermDebt"),
                operating_cash_flow=self._extract_financial(stock, "operatingCashFlow"),
                free_cash_flow=self._extract_financial(stock, "freeCashFlow"),
                
                # Ratios & Margins
                profit_margin=info.get("profitMargins"),
                operating_margin=info.get("operatingMargins"),
                return_on_equity=info.get("returnOnEquity"),
                return_on_assets=info.get("returnOnAssets"),
                debt_to_equity=info.get("debtToEquity"),
                current_ratio=info.get("currentRatio"),
                quick_ratio=info.get("quickRatio"),
                price_to_book=info.get("priceToBook"),
                price_to_sales=info.get("priceToSalesTrailing12Months"),
                
                # Growth metrics
                revenue_growth=info.get("revenueGrowth"),
                earnings_growth=info.get("earningsGrowth"),
                
                # Historical prices
                price_history=history if not history.empty else None,
                
                # Technical indicators (computed)
                rsi=tech.get("rsi"),
                sma_20=tech.get("sma_20"),
                sma_50=tech.get("sma_50"),
                sma_200=tech.get("sma_200"),
                ema_12=tech.get("ema_12"),
                ema_26=tech.get("ema_26"),
                atr=tech.get("atr"),
                macd=tech.get("macd"),
                macd_signal=tech.get("macd_signal"),
                bollinger_upper=tech.get("bollinger_upper"),
                bollinger_lower=tech.get("bollinger_lower"),
                
                # Meta
                data_source=self.name,
                last_updated=datetime.utcnow(),
                currency=info.get("currency") or "USD",
            )
            
            logger.info(f"Fetched data for {ticker} from yfinance")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch {ticker} from yfinance: {str(e)}")
            return None
    
    def fetch_price(self, ticker: str) -> Optional[float]:
        """Fetch current price only."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info.get("regularMarketPrice")
        except Exception as e:
            logger.error(f"Failed to fetch price for {ticker}: {str(e)}")
            return None
    
    def fetch_fundamentals(self, ticker: str) -> dict:
        """Fetch fundamental metrics only."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                "pe_ratio": info.get("trailingPE"),
                "eps": info.get("trailingEps"),
                "beta": info.get("beta"),
                "dividend_yield": info.get("dividendYield"),
                "market_cap": info.get("marketCap"),
                "revenue": info.get("totalRevenue"),
                "profit_margin": info.get("profitMargins"),
            }
        except Exception as e:
            logger.error(f"Failed to fetch fundamentals for {ticker}: {str(e)}")
            return {}
    
    def fetch_history(self, ticker: str, period: str = "1y") -> dict:
        """Fetch historical price data."""
        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period=period)
            return {
                "df": history,
                "period": period,
                "count": len(history)
            }
        except Exception as e:
            logger.error(f"Failed to fetch history for {ticker}: {str(e)}")
            return {}
    
    def _compute_technicals(self, df: pd.DataFrame) -> dict:
        """Compute technical indicators from price history."""
        if df is None or df.empty or len(df) < 20:
            return {}
        
        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        
        tech = {}
        
        # RSI (14-period)
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        tech["rsi"] = (100 - (100 / (1 + rs))).iloc[-1] if not rs.isna().iloc[-1] else None
        
        # Moving averages
        tech["sma_20"] = close.rolling(20).mean().iloc[-1] if len(close) >= 20 else None
        tech["sma_50"] = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else None
        tech["sma_200"] = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None
        
        # EMAs
        tech["ema_12"] = close.ewm(span=12).mean().iloc[-1]
        tech["ema_26"] = close.ewm(span=26).mean().iloc[-1]
        
        # ATR (14-period)
        tr = pd.concat([
            high - low,
            abs(high - close.shift()),
            abs(low - close.shift())
        ], axis=1).max(axis=1)
        tech["atr"] = tr.rolling(14).mean().iloc[-1] if len(tr) >= 14 else None
        
        # MACD
        tech["macd"] = (tech.get("ema_12") - tech.get("ema_26")) if tech.get("ema_12") and tech.get("ema_26") else None
        tech["macd_signal"] = None  # Would need full series for signal line
        
        # Bollinger Bands (20-period, 2 std)
        rolling_mean = close.rolling(20).mean() if len(close) >= 20 else close
        rolling_std = close.rolling(20).std() if len(close) >= 20 else 0
        tech["bollinger_upper"] = (rolling_mean.iloc[-1] + 2 * rolling_std.iloc[-1]) if len(close) >= 20 else None
        tech["bollinger_lower"] = (rolling_mean.iloc[-1] - 2 * rolling_std.iloc[-1]) if len(close) >= 20 else None
        
        return tech
    
    def _extract_financial(self, stock: yf.Ticker, field: str) -> Optional[float]:
        """Extract single financial metric from balance sheet/income statement."""
        try:
            financials = stock.balance_sheet if "Assets" in field or "Liabilities" in field or "Equity" in field else stock.financials
            if financials is not None and not financials.empty:
                return financials[field].iloc[0] if field in financials.index else None
        except:
            pass
        return None
    
    def _parse_date(self, timestamp: Optional[int]) -> Optional[datetime]:
        """Convert Unix timestamp to datetime."""
        if timestamp is None:
            return None
        try:
            return datetime.utcfromtimestamp(timestamp)
        except:
            return None