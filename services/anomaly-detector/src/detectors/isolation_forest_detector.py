import pandas as pd
import numpy as np
from typing import List, Dict, Any
from sklearn.ensemble import IsolationForest
from .base import BaseDetector
import structlog

logger = structlog.get_logger()


class IsolationForestDetector(BaseDetector):
    """
    Detect anomalies using Isolation Forest (ML-based)
    
    Unsupervised learning algorithm that isolates anomalies
    by randomly selecting features and split values.
    """
    
    def __init__(self, contamination: float = 0.1, n_estimators: int = 100):
        """
        Args:
            contamination: Expected proportion of anomalies (default: 0.1 = 10%)
            n_estimators: Number of trees in the forest (default: 100)
        """
        super().__init__("isolation_forest")
        self.contamination = contamination
        self.n_estimators = n_estimators
        
        logger.info(
            f"IsolationForestDetector initialized",
            contamination=contamination,
            n_estimators=n_estimators
        )
    
    def detect(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies using Isolation Forest"""
        
        if not self.validate_data(df):
            return []
        
        if len(df) < 30:  # Need minimum data for ML
            logger.warning(
                f"{self.name}: Insufficient data points",
                data_points=len(df),
                required=30
            )
            return []
        
        # Calculate features
        df = self.calculate_returns(df)
        df = df.dropna(subset=['daily_return'])
        
        if df.empty:
            return []
        
        symbol = df['symbol'].iloc[0]
        
        # Create feature matrix
        # Features: daily_return, volume_change, price_range
        df['volume_change'] = df['volume'].pct_change() * 100
        df['price_range'] = (df['high'] - df['low']) / df['close'] * 100
        
        # Drop NaN rows
        df = df.dropna(subset=['daily_return', 'volume_change', 'price_range'])
        
        if len(df) < 30:
            return []
        
        # Prepare features
        features = df[['daily_return', 'volume_change', 'price_range']].values
        
        # Train Isolation Forest
        iso_forest = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=42,
            n_jobs=-1
        )
        
        # Predict (-1 for anomalies, 1 for normal)
        predictions = iso_forest.fit_predict(features)
        
        # Get anomaly scores (lower = more anomalous)
        scores = iso_forest.score_samples(features)
        
        # Add to dataframe
        df['is_anomaly'] = predictions == -1
        df['anomaly_score'] = -scores  # Flip sign so higher = more anomalous
        
        # Normalize scores to 0-10 range
        if df['anomaly_score'].max() > df['anomaly_score'].min():
            df['normalized_score'] = (
                (df['anomaly_score'] - df['anomaly_score'].min()) / 
                (df['anomaly_score'].max() - df['anomaly_score'].min()) * 10
            )
        else:
            df['normalized_score'] = 0
        
        # Extract anomalies
        anomalies = []
        anomaly_df = df[df['is_anomaly']].copy()
        
        for _, row in anomaly_df.iterrows():
            anomaly = {
                'symbol': symbol,
                'timestamp': row['timestamp'],
                'anomaly_type': 'multivariate',
                'method': self.name,
                'score': float(row['normalized_score']),
                'details': {
                    'daily_return': float(row['daily_return']),
                    'volume_change': float(row['volume_change']),
                    'price_range': float(row['price_range']),
                    'raw_score': float(row['anomaly_score']),
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