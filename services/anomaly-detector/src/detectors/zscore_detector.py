import pandas as pd
import numpy as np
from typing import List, Dict, Any
from .base import BaseDetector
import structlog

logger = structlog.get_logger()


class ZScoreDetector(BaseDetector):
    """
    Detect anomalies using Z-score method on daily returns
    
    An anomaly is flagged when |z-score| > threshold, where:
    z-score = (value - rolling_mean) / rolling_std
    """
    
    def __init__(self, threshold: float = 3.0, window: int = 30):
        """
        Args:
            threshold: Z-score threshold for anomaly detection (default: 3.0)
            window: Rolling window size for calculating mean/std (default: 30 days)
        """
        super().__init__("zscore")
        self.threshold = threshold
        self.window = window
        
        logger.info(
            f"ZScoreDetector initialized",
            threshold=threshold,
            window=window
        )
    
    def detect(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect anomalies using Z-score method
        
        Args:
            df: DataFrame with stock price data
            
        Returns:
            List of detected anomalies
        """
        # Validate input data
        if not self.validate_data(df):
            return []
        
        if len(df) < self.window:
            logger.warning(
                f"{self.name}: Insufficient data points",
                data_points=len(df),
                required=self.window
            )
            return []
        
        # Calculate daily returns
        df = self.calculate_returns(df)
        df = df.dropna(subset=['daily_return'])
        
        if df.empty:
            return []
        
        symbol = df['symbol'].iloc[0]
        
        # Calculate rolling statistics
        df['rolling_mean'] = df['daily_return'].rolling(
            window=self.window,
            min_periods=self.window
        ).mean()
        
        df['rolling_std'] = df['daily_return'].rolling(
            window=self.window,
            min_periods=self.window
        ).std()
        
        # Calculate z-score
        df['zscore'] = (df['daily_return'] - df['rolling_mean']) / df['rolling_std']
        
        # Flag anomalies
        df['is_anomaly'] = np.abs(df['zscore']) > self.threshold
        
        # Extract anomalies
        anomalies = []
        anomaly_df = df[df['is_anomaly']].copy()
        
        for _, row in anomaly_df.iterrows():
            anomaly = {
                'symbol': symbol,
                'timestamp': row['timestamp'],
                'anomaly_type': 'price_movement',
                'method': self.name,
                'score': float(abs(row['zscore'])),
                'details': {
                    'daily_return': float(row['daily_return']),
                    'zscore': float(row['zscore']),
                    'rolling_mean': float(row['rolling_mean']),
                    'rolling_std': float(row['rolling_std']),
                    'threshold': self.threshold,
                    'close_price': float(row['close']),
                    'direction': 'spike' if row['daily_return'] > 0 else 'drop'
                }
            }
            anomalies.append(anomaly)
        
        if anomalies:
            logger.info(
                f"Detected {len(anomalies)} anomalies for {symbol}",
                symbol=symbol,
                method=self.name,
                count=len(anomalies)
            )
        
        return anomalies