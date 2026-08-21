"""Abstract base class for all data adapters."""
from abc import ABC, abstractmethod
from typing import Optional
from ..models.stock_data import StockData


class DataAdapter(ABC):
    """
    Abstract base class for data source adapters.
    
    All adapters MUST implement these methods. This ensures your screener
    can work with any data source interchangeably.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this data source."""
        pass
    
    @property
    @abstractmethod
    def supports(self) -> list:
        """List of data types this adapter can fetch."""
        # e.g., ["price", "fundamentals", "history", "metadata"]
        pass
    
    @abstractmethod
    def fetch(self, ticker: str, **kwargs) -> Optional[StockData]:
        """
        Fetch all available data for a ticker.
        
        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            **kwargs: Additional parameters (e.g., timeframe, interval)
            
        Returns:
            StockData object with all available fields populated
            
        Raises:
            DataFetchError: If the fetch fails
        """
        pass
    
    @abstractmethod
    def fetch_price(self, ticker: str) -> Optional[float]:
        """Fetch current price only."""
        pass
    
    @abstractmethod
    def fetch_fundamentals(self, ticker: str) -> dict:
        """Fetch fundamental metrics only."""
        pass
    
    @abstractmethod
    def fetch_history(self, ticker: str, period: str = "1y") -> dict:
        """Fetch historical price data."""
        pass
    
    def validate_ticker(self, ticker: str) -> bool:
        """Validate ticker format before fetching."""
        if not ticker or not isinstance(ticker, str):
            return False
        if len(ticker) > 10:
            return False  # Very long tickers are suspicious
        if ticker.startswith("^"):  # Index symbols
            return True
        if "." in ticker:  # Already has exchange prefix
            return True
        return True  # Assume valid unless proven otherwise