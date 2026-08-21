"""Screening/filtering logic for stocks."""
import logging
from typing import List, Optional, Callable
from ..models.stock_data import StockData

logger = logging.getLogger(__name__)


class StockScreener:
    """
    Applies filters to stock data to find matching opportunities.
    
    In Phase 1, this is a simple filter engine. Later phases will add
    multi-factor scoring, backtesting, and risk calculations.
    """
    
    def __init__(self):
        self.filters: List[Callable[[StockData], bool]] = []
    
    def add_filter(self, condition: Callable[[StockData], bool]):
        """Add a screening condition."""
        self.filters.append(condition)
        logger.info(f"Added filter: {condition.__name__}")
    
    def clear_filters(self):
        """Remove all filters."""
        self.filters.clear()
    
    def screen(self, stocks: List[Optional[StockData]]) -> List[StockData]:
        """
        Apply all filters to a list of stocks.
        
        Args:
            stocks: List of StockData objects (may contain None)
            
        Returns:
            Filtered list containing only stocks that pass all conditions
        """
        results = []
        for stock in stocks:
            if stock is None:
                continue
            if all(condition(stock) for condition in self.filters):
                results.append(stock)
        return results
    
    # Preset filter builders
    
    def value_filter(self, max_pe: float = 20.0, max_pb: float = 3.0) -> 'StockScreener':
        """Add value investing filters."""
        def condition(stock: StockData) -> bool:
            pe = stock.pe_ratio or float('inf')
            pb = stock.price_to_book or float('inf')
            return pe <= max_pe and pb <= max_pb
        self.add_filter(condition)
        return self
    
    def momentum_filter(self, min_rsi: float = 30.0, max_rsi: float = 70.0) -> 'StockScreener':
        """Add momentum filters."""
        def condition(stock: StockData) -> bool:
            rsi = stock.rsi
            if rsi is None:
                return True  # Skip if no data
            return min_rsi <= rsi <= max_rsi
        self.add_filter(condition)
        return self
    
    def profitability_filter(self, min_margin: float = 0.1) -> 'StockScreener':
        """Filter by profit margin."""
        def condition(stock: StockData) -> bool:
            margin = stock.profit_margin
            if margin is None:
                return True
            return margin >= min_margin
        self.add_filter(condition)
        return self
    
    def size_filter(self, min_market_cap: float = 1e9, max_market_cap: Optional[float] = None) -> 'StockScreener':
        """Filter by market cap."""
        def condition(stock: StockData) -> bool:
            cap = stock.market_cap
            if cap is None:
                return True
            if cap < min_market_cap:
                return False
            if max_market_cap and cap > max_market_cap:
                return False
            return True
        self.add_filter(condition)
        return self