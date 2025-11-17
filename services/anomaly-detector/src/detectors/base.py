from abc import ABC, abstractmethod
import pandas as pd
from typing import List, Dict, Any
import structlog

logger = structlog.get_logger()


class BaseDetector(ABC):
    """Base class for all anomaly detectors"""
    
    def __init__(self, name: str):
        self.name = name
        logger.info(f"Initialized {self.name} detector")
    
    @abstractmethod
    def detect(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect anomalies in the data
        
        Args:
            df: DataFrame with columns [symbol, timestamp, open, high, low, close, volume]
            
        Returns:
            List of anomaly dictionaries with structure:
            {
                'symbol': str,
                'timestamp': datetime,
                'anomaly_type': str,
                'method': str,
                'score': float,
                'details': dict
            }
        """
        pass
    
    def calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate daily returns (percentage change in close price)
        
        Args:
            df: DataFrame with 'close' column
            
        Returns:
            DataFrame with added 'daily_return' column
        """
        df = df.copy()
        df['daily_return'] = df['close'].pct_change() * 100  # Convert to percentage
        return df
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validate that DataFrame has required columns and sufficient data
        
        Args:
            df: DataFrame to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_columns = ['symbol', 'timestamp', 'close']
        
        if df.empty:
            logger.warning(f"{self.name}: DataFrame is empty")
            return False
        
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            logger.warning(f"{self.name}: Missing columns: {missing_cols}")
            return False
        
        return True