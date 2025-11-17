import pandas as pd
import numpy as np
from typing import List, Dict, Any
from .base import BaseDetector
import structlog

logger = structlog.get_logger()


class MovingAverageDetector(BaseDetector):
    """
    Detect anomalies when price deviates significantly from moving average
    
    Simple trend-following method. Flags when price moves >X% from MA.
    """
    
    def __init__(self, window: int = 20, threshold_pct: float = 5.0):
        """
        Args:
            window: Moving average window (default: 20 days)
            threshold_pct: Deviation threshold in % (default: 5%)
        """
        super().__init__("moving_average")
        self.window = window
        self.threshold_pct = threshold_pct
        
        logger.info(
            f"MovingAverageDetector initialized",
            window=window,
            threshold_pct=threshold_pct
        )
    
    def detect(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies using Moving Average deviation"""
        
        if not self.validate_data(df):
            return []
        
        if len(df) < self.window:
            logger.warning(
                f"{self.name}: Insufficient data points",
                data_points=len(df),
                required=self.window
            )
            return []
        
        symbol = df['symbol'].iloc[0]
        
        # Calculate moving average
        df['ma'] = df['close'].rolling(window=self.window, min_periods=self.window).mean()
        
        # Calculate deviation percentage
        df['deviation_pct'] = ((df['close'] - df['ma']) / df['ma'] * 100)
        
        # Flag anomalies
        df['is_anomaly'] = np.abs(df['deviation_pct']) > self.threshold_pct
        
        # Calculate score (normalized deviation)
        df['score'] = np.abs(df['deviation_pct']) / self.threshold_pct
        
        # Extract anomalies
        anomalies = []
        anomaly_df = df[df['is_anomaly']].copy()
        
        for _, row in anomaly_df.iterrows():
            anomaly = {
                'symbol': symbol,
                'timestamp': row['timestamp'],
                'anomaly_type': 'trend_deviation',
                'method': self.name,
                'score': float(row['score']),
                'details': {
                    'close_price': float(row['close']),
                    'moving_average': float(row['ma']),
                    'deviation_pct': float(row['deviation_pct']),
                    'threshold_pct': self.threshold_pct,
                    'direction': 'above' if row['deviation_pct'] > 0 else 'below'
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