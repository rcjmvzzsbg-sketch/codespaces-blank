"""Orchestrates data fetching from adapters."""
import logging
from typing import List, Optional

from ..adapters.base import DataAdapter
from ..adapters.yfinance_adapter import YFinanceAdapter
from ..models.stock_data import StockData

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Orchestrates data fetching from one or more adapters.
    
    In Phase 1, uses only yfinance. Later phases will add
    Stooq, SEC EDGAR, and Google Sheets adapters.
    """
    
    def __init__(self, default_source: str = "yfinance"):
        self.default_source = default_source
        self.adapters: dict[str, DataAdapter] = {}
        
        # Register default adapter
        self.register_adapter(YFinanceAdapter())
    
    def register_adapter(self, adapter: DataAdapter):
        """Register a data source adapter."""
        self.adapters[adapter.name.lower()] = adapter
        logger.info(f"Registered adapter: {adapter.name}")
    
    def fetch(self, ticker: str, source: Optional[str] = None) -> Optional[StockData]:
        """
        Fetch stock data using specified or default adapter.
        
        Args:
            ticker: Stock ticker symbol
            source: Adapter name (case-insensitive), uses default if None
            
        Returns:
            StockData object or None if fetch fails
        """
        source = source or self.default_source
        source_key = source.lower()
        
        if source_key not in self.adapters:
            logger.error(f"Unknown adapter: {source}. Available: {list(self.adapters.keys())}")
            return None
        
        adapter = self.adapters[source_key]
        return adapter.fetch(ticker)
    
    def fetch_multiple(self, tickers: List[str], source: Optional[str] = None) -> List[StockData]:
        """
        Fetch data for multiple tickers.
        
        Args:
            tickers: List of ticker symbols
            source: Adapter to use
            
        Returns:
            List of StockData objects (may contain None for failed fetches)
        """
        results = []
        for ticker in tickers:
            try:
                data = self.fetch(ticker, source)
                results.append(data)
            except Exception as e:
                logger.error(f"Failed to fetch {ticker}: {str(e)}")
                results.append(None)
        return results
    
    def list_sources(self) -> List[str]:
        """Return list of available data sources."""
        return list(self.adapters.keys())