#!/usr/bin/env python3
"""CLI entry point for stock screener."""
import argparse
import logging
import sys
from datetime import datetime

from config.settings import DEFAULT_SOURCE, DEFAULT_OUTPUT_FORMAT
from adapters import YFinanceAdapter
from core.fetcher import DataFetcher
from core.screener import StockScreener
from utils.formatters import format_table, format_json, format_full_report
from models.stock_data import StockData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Stock Screener - Phase 1 (yfinance)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--ticker", "-t",
        nargs="+",
        required=True,
        help="Stock ticker symbol(s) (e.g., AAPL MSFT GOOGL)"
    )
    
    parser.add_argument(
        "--source", "-s",
        default=DEFAULT_SOURCE,
        choices=["yfinance"],
        help=f"Data source (default: {DEFAULT_SOURCE})"
    )
    
    parser.add_argument(
        "--output", "-o",
        default=DEFAULT_OUTPUT_FORMAT,
        choices=["table", "json", "report"],
        help=f"Output format (default: {DEFAULT_OUTPUT_FORMAT})"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Stock Screener - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Fetching {len(args.ticker)} ticker(s) from {args.source}")
    
    # Initialize fetcher
    fetcher = DataFetcher(default_source=args.source)
    
    # Fetch data
    tickers = [t.upper() for t in args.ticker]
    results = fetcher.fetch_multiple(tickers, args.source)
    
    # Filter out failures
    successful = [r for r in results if r is not None]
    failed = [t for t, r in zip(tickers, results) if r is None]
    
    if failed:
        logger.warning(f"Failed to fetch: {', '.join(failed)}")
    
    if not successful:
        print("No data retrieved. Check ticker symbols and network connection.")
        sys.exit(1)
    
    # Output results
    if args.output == "table":
        print(format_table(successful))
    elif args.output == "json":
        print(format_json(successful))
    elif args.output == "report":
        for stock in successful:
            print(format_full_report(stock))
            print("\n" + "="*50 + "\n")
    
    # Summary
    logger.info(f"Successfully fetched {len(successful)} / {len(results)} stocks")


if __name__ == "__main__":
    main()