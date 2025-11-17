import pandas as pd
import numpy as np
from typing import List, Dict, Any
from .base import BaseDetector
import structlog

logger = structlog.get_logger()


class IQRDetector(BaseDetector):
    """
    Detect anomalies using Interquartile Range (IQR) method
    
    Simpler and more robust to extreme values than Z-score.
    Flags values outside Q1 - 1.5*IQR or Q3 + 1.5*IQR
    """
    
    def __init__(self, multiplier: float = 1.5, window: int = 30):
        """
        Args:
            multiplier: IQR multiplier for bounds (default: 1.5)
            window: Rolling window for IQR calculation (default: 30)
        """
        super().__init__("iqr")
        self.multiplier = multiplier
        self.window = window
        
        logger.info(
            f"IQRDetector initialized",
            multiplier=multiplier,
            window=window
        )
    
    def detect(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies using IQR method"""
        
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
        
        # Calculate rolling IQR
        df['rolling_q1'] = df['daily_return'].rolling(
            window=self.window,
            min_periods=self.window
        ).quantile(0.25)
        
        df['rolling_q3'] = df['daily_return'].rolling(
            window=self.window,
            min_periods=self.window
        ).quantile(0.75)
        
        df['iqr'] = df['rolling_q3'] - df['rolling_q1']
        
        # Calculate bounds
        df['lower_bound'] = df['rolling_q1'] - (self.multiplier * df['iqr'])
        df['upper_bound'] = df['rolling_q3'] + (self.multiplier * df['iqr'])
        
        # Flag anomalies
        df['is_anomaly'] = (
            (df['daily_return'] < df['lower_bound']) | 
            (df['daily_return'] > df['upper_bound'])
        )
        
        # Calculate anomaly score (distance from nearest bound)
        df['score'] = df.apply(
            lambda row: abs(row['daily_return'] - row['lower_bound']) / row['iqr']
            if row['daily_return'] < row['lower_bound']
            else abs(row['daily_return'] - row['upper_bound']) / row['iqr']
            if row['daily_return'] > row['upper_bound']
            else 0,
            axis=1
        )
        
        # Extract anomalies
        anomalies = []
        anomaly_df = df[df['is_anomaly']].copy()
        
        for _, row in anomaly_df.iterrows():
            anomaly = {
                'symbol': symbol,
                'timestamp': row['timestamp'],
                'anomaly_type': 'price_movement',
                'method': self.name,
                'score': float(row['score']),
                'details': {
                    'daily_return': float(row['daily_return']),
                    'iqr': float(row['iqr']),
                    'lower_bound': float(row['lower_bound']),
                    'upper_bound': float(row['upper_bound']),
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