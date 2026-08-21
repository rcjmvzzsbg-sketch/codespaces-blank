"""Unit tests for data adapters."""
import pytest
from stock_screener.adapters.yfinance_adapter import YFinanceAdapter
from stock_screener.models.stock_data import StockData


class TestYFinanceAdapter:
    """Tests for yfinance adapter."""
    
    def setup_method(self):
        self.adapter = YFinanceAdapter()
    
    def test_valid_ticker(self):
        """Test fetching valid ticker."""
        data = self.adapter.fetch("AAPL")
        assert data is not None
        assert data.ticker == "AAPL"
        assert data.current_price is not None
        assert data.current_price > 0
    
    def test_invalid_ticker(self):
        """Test fetching invalid ticker returns None."""
        data = self.adapter.fetch("INVALID123456")
        assert data is None
    
    def test_fetch_price_only(self):
        """Test price-only fetch."""
        price = self.adapter.fetch_price("MSFT")
        assert price is not None
        assert price > 0
    
    def test_fetch_fundamentals(self):
        """Test fundamentals fetch."""
        funds = self.adapter.fetch_fundamentals("GOOGL")
        assert "pe_ratio" in funds
        assert "market_cap" in funds
    
    def test_fetch_history(self):
        """Test historical data fetch."""
        history = self.adapter.fetch_history("TSLA", period="1mo")
        assert "df" in history
        assert "count" in history
        assert history["count"] > 0
    
    def test_supported_features(self):
        """Test adapter reports correct capabilities."""
        assert "price" in self.adapter.supports
        assert "fundamentals" in self.adapter.supports
        assert "history" in self.adapter.supports


if __name__ == "__main__":
    pytest.main([__file__, "-v"])