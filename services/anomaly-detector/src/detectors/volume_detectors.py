import pandas as pd
import numpy as np
from typing import List, Dict, Any
from .base import BaseDetector
import structlog

logger = structlog.get_logger()


class VolumeAnomalyDetector(BaseDetector):
    """
    Detect anomalies in trading volume
    
    Unusual volume often precedes or accompanies price movements.
    Uses Z-score on volume changes.
    """
    
    def __init__(self, threshold: float = 3.0, window: int = 20):
        """
        Args:
            threshold: Z-score threshold (default: 3.0)
            window: Rolling window for statistics (default: 20)
        """
        super().__init__("volume_anomaly")
        self.threshold = threshold
        self.window = window
        
        logger.info(
            f"VolumeAnomalyDetector initialized",
            threshold=threshold,
            window=window
        )
    
    def detect(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect volume anomalies"""
        
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
        
        # Calculate volume change percentage
        df['volume_change'] = df['volume'].pct_change() * 100
        
        # Rolling statistics
        df['volume_mean'] = df['volume_change'].rolling(
            window=self.window, 
            min_periods=self.window
        ).mean()
        
        df['volume_std'] = df['volume_change'].rolling(
            window=self.window,
            min_periods=self.window
        ).std()
        
        # Z-score
        df['volume_zscore'] = (
            (df['volume_change'] - df['volume_mean']) / df['volume_std']
        )
        
        # Flag anomalies
        df['is_anomaly'] = np.abs(df['volume_zscore']) > self.threshold
        
        # Extract anomalies
        anomalies = []
        anomaly_df = df[df['is_anomaly']].copy()
        
        for _, row in anomaly_df.iterrows():
            # Also get price change on same day for context
            price_change = row['close'] - df.loc[df['timestamp'] < row['timestamp'], 'close'].iloc[-1] if len(df[df['timestamp'] < row['timestamp']]) > 0 else 0
            price_change_pct = (price_change / df.loc[df['timestamp'] < row['timestamp'], 'close'].iloc[-1] * 100) if len(df[df['timestamp'] < row['timestamp']]) > 0 else 0
            
            anomaly = {
                'symbol': symbol,
                'timestamp': row['timestamp'],
                'anomaly_type': 'volume_spike',
                'method': self.name,
                'score': float(abs(row['volume_zscore'])),
                'details': {
                    'volume': int(row['volume']),
                    'volume_change_pct': float(row['volume_change']),
                    'volume_zscore': float(row['volume_zscore']),
                    'price_change_pct': float(price_change_pct),
                    'direction': 'spike' if row['volume_change'] > 0 else 'drop',
                    'close_price': float(row['close'])
                }
            }
            anomalies.append(anomaly)
        
        if anomalies:
            logger.info(
                f"Detected {len(anomalies)} volume anomalies for {symbol}",
                symbol=symbol,
                method=self.name,
                count=len(anomalies)
            )
        
        return anomalies