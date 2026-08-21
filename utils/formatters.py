"""Output formatting utilities."""
import json
from typing import List
import pandas as pd
from tabulate import tabulate
from ..models.stock_data import StockData


def format_table(stocks: List[StockData]) -> str:
    """Format stocks as a markdown-style table."""
    if not stocks:
        return "No stocks matched your criteria."
    
    headers = ["Ticker", "Name", "Price", "P/E", "Market Cap", "RSI", "SMA 50"]
    rows = []
    
    for stock in stocks:
        row = [
            stock.ticker,
            stock.company_name[:25] + "..." if len(stock.company_name) > 25 else stock.company_name,
            f"${stock.current_price:,.2f}" if stock.current_price else "N/A",
            f"{stock.pe_ratio:.2f}" if stock.pe_ratio else "N/A",
            f"${stock.market_cap/1e9:.1f}B" if stock.market_cap else "N/A",
            f"{stock.rsi:.1f}" if stock.rsi else "N/A",
            f"${stock.sma_50:.2f}" if stock.sma_50 else "N/A",
        ]
        rows.append(row)
    
    return tabulate(rows, headers=headers, tablefmt="grid")


def format_json(stocks: List[StockData], indent: int = 2) -> str:
    """Format stocks as JSON."""
    data = [stock.to_dict() for stock in stocks]
    return json.dumps(data, indent=indent, default=str)


def format_full_report(stock: StockData) -> str:
    """Generate full formatted report for single stock."""
    lines = [
        "# Stock Analysis Report",
        "",
        f"## {stock.ticker}: {stock.company_name}",
        "",
        "### Company Info",
        f"- Exchange: {stock.exchange}",
        f"- Sector: {stock.sector or 'N/A'}",
        f"- Industry: {stock.industry or 'N/A'}",
        "",
        "### Price Data",
        f"| Metric | Value |",
        f"|--------|-------|",
    ]
    
    if stock.current_price:
        lines.append(f"| Current Price | ${stock.current_price:,.2f} |")
    if stock.previous_close:
        lines.append(f"| Previous Close | ${stock.previous_close:,.2f} |")
    if stock.day_high:
        lines.append(f"| Day High | ${stock.day_high:,.2f} |")
    if stock.day_low:
        lines.append(f"| Day Low | ${stock.day_low:,.2f} |")
    if stock.volume:
        lines.append(f"| Volume | {stock.volume:,} |")
    if stock.market_cap:
        lines.append(f"| Market Cap | ${stock.market_cap:,.0f} |")
    
    lines.extend([
        "",
        "### Fundamentals",
        f"| Metric | Value |",
        f"|--------|-------|",
    ])
    
    if stock.pe_ratio:
        lines.append(f"| P/E Ratio | {stock.pe_ratio:.2f} |")
    if stock.eps:
        lines.append(f"| EPS | ${stock.eps:.2f} |")
    if stock.beta:
        lines.append(f"| Beta | {stock.beta:.2f} |")
    if stock.dividend_yield:
        lines.append(f"| Dividend Yield | {stock.dividend_yield:.2%} |")
    if stock.revenue:
        lines.append(f"| Revenue | ${stock.revenue:,.0f} |")
    if stock.net_income:
        lines.append(f"| Net Income | ${stock.net_income:,.0f} |")
    
    lines.extend([
        "",
        "### Technical Indicators",
        f"| Metric | Value |",
        f"|--------|-------|",
    ])
    
    if stock.rsi:
        lines.append(f"| RSI (14) | {stock.rsi:.1f} |")
    if stock.sma_50:
        lines.append(f"| SMA 50 | ${stock.sma_50:.2f} |")
    if stock.sma_200:
        lines.append(f"| SMA 200 | ${stock.sma_200:.2f} |")
    if stock.atr:
        lines.append(f"| ATR (14) | ${stock.atr:.2f} |")
    
    lines.extend([
        "",
        f"*Data Source: {stock.data_source}* | *Last Updated: {stock.last_updated.strftime('%Y-%m-%d %H:%M:%S')}*",
    ])
    
    return "\n".join(lines)