import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import structlog
import time

logger = structlog.get_logger()


class DataFetcher:
    """Fetch stock market data from yfinance"""
    
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        logger.info(f"Initialized DataFetcher with {len(symbols)} symbols")
    
    def fetch_historical_data(
        self, 
        symbol: str, 
        days: int = 365
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical data for a single symbol
        
        Args:
            symbol: Stock ticker symbol
            days: Number of days of historical data
            
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            logger.info(f"Fetching {days} days of data for {symbol}")
            
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Fetch historical data
            df = ticker.history(start=start_date, end=end_date, interval="1d")
            
            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return None
            
            # Clean and prepare data
            df = df.reset_index()
            df['symbol'] = symbol
            
            # Rename columns to match our schema
            df = df.rename(columns={
                'Date': 'timestamp',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Select only columns we need
            df = df[['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            # Convert timestamp to datetime (remove timezone info for postgres)
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
            
            # Remove any rows with NaN in critical columns
            df = df.dropna(subset=['close'])
            
            logger.info(
                f"Successfully fetched {len(df)} records for {symbol}",
                date_range=f"{df['timestamp'].min()} to {df['timestamp'].max()}"
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}", error=str(e))
            return None
    
    def fetch_all_symbols(
        self, 
        days: int = 365,
        delay_seconds: float = 1.0
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for all configured symbols
        
        Args:
            days: Number of days of historical data
            delay_seconds: Delay between requests to avoid rate limiting
            
        Returns:
            Dictionary mapping symbol to DataFrame
        """
        results = {}
        
        for i, symbol in enumerate(self.symbols, 1):
            logger.info(
                f"Fetching symbol {i}/{len(self.symbols)}: {symbol}"
            )
            
            df = self.fetch_historical_data(symbol, days)
            
            if df is not None and not df.empty:
                results[symbol] = df
            
            # Add delay between requests to be nice to the API
            if i < len(self.symbols):
                time.sleep(delay_seconds)
        
        logger.info(
            f"Fetch complete: {len(results)}/{len(self.symbols)} symbols successful"
        )
        
        return results
    
    def get_latest_data(self, symbol: str) -> Optional[Dict]:
        """
        Get just the latest data point for a symbol
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with latest OHLCV data or None
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1d", interval="1d")
            
            if df.empty:
                return None
            
            latest = df.iloc[-1]
            
            return {
                'symbol': symbol,
                'timestamp': df.index[-1].to_pydatetime().replace(tzinfo=None),
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'close': float(latest['Close']),
                'volume': int(latest['Volume'])
            }
            
        except Exception as e:
            logger.error(f"Error fetching latest data for {symbol}", error=str(e))
            return None