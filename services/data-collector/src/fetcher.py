import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import structlog
import time
import requests

logger = structlog.get_logger()


class DataFetcher:
    """Fetch stock market data from yfinance"""
    
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        
        # Set user agent to avoid being blocked
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        logger.info(f"Initialized DataFetcher with {len(symbols)} symbols")
    
    def fetch_historical_data(
        self, 
        symbol: str, 
        days: int = 365,
        max_retries: int = 3
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical data for a single symbol with retry logic
        
        Args:
            symbol: Stock ticker symbol
            days: Number of days of historical data
            max_retries: Maximum number of retry attempts
            
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Fetching {days} days of data for {symbol}",
                    attempt=attempt + 1,
                    max_retries=max_retries
                )
                
                # Use session for better reliability
                ticker = yf.Ticker(symbol, session=self.session)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                # Fetch historical data
                df = ticker.history(
                    start=start_date, 
                    end=end_date, 
                    interval="1d",
                    auto_adjust=True,  # Adjust for splits/dividends
                    actions=False      # Don't include dividends/splits
                )
                
                if df.empty:
                    logger.warning(f"No data returned for {symbol}")
                    
                    # Retry with shorter period
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
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
                    records=len(df),
                    date_range=f"{df['timestamp'].min()} to {df['timestamp'].max()}"
                )
                
                return df
                
            except Exception as e:
                logger.error(
                    f"Error fetching data for {symbol}",
                    symbol=symbol,
                    attempt=attempt + 1,
                    error=str(e)
                )
                
                # Wait before retry (exponential backoff)
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch {symbol} after {max_retries} attempts")
                    return None
        
        return None
    
    def fetch_all_symbols(
        self, 
        days: int = 365,
        delay_seconds: float = 2.0  # Increased delay
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
            else:
                logger.warning(f"Skipping {symbol} - no data available")
            
            # Add delay between requests to be nice to the API
            if i < len(self.symbols):
                logger.info(f"Waiting {delay_seconds}s before next request...")
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
            ticker = yf.Ticker(symbol, session=self.session)
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