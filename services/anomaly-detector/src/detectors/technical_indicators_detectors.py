import pandas as pd
import numpy as np
from typing import List, Dict, Any
from .base import BaseDetector
import structlog

logger = structlog.get_logger()


class TechnicalIndicatorsDetector(BaseDetector):
    """
    Detect anomalies using technical indicators
    
    Monitors RSI (overbought/oversold) and Bollinger Bands breaches
    """
    
    def __init__(self, rsi_period: int = 14, bb_period: int = 20, bb_std: float = 2.0):
        """
        Args:
            rsi_period: RSI calculation period (default: 14)
            bb_period: Bollinger Bands period (default: 20)
            bb_std: Bollinger Bands std deviation (default: 2.0)
        """
        super().__init__("technical_indicators")
        self.rsi_period = rsi_period
        self.bb_period = bb_period
        self.bb_std = bb_std
        
        logger.info(
            f"TechnicalIndicatorsDetector initialized",
            rsi_period=rsi_period,
            bb_period=bb_period,
            bb_std=bb_std
        )
    
    def calculate_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI indicator"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        return df
    
    def calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands"""
        df['bb_middle'] = df['close'].rolling(window=self.bb_period).mean()
        df['bb_std'] = df['close'].rolling(window=self.bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (self.bb_std * df['bb_std'])
        df['bb_lower'] = df['bb_middle'] - (self.bb_std * df['bb_std'])
        return df
    
    def detect(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect technical indicator anomalies"""
        
        if not self.validate_data(df):
            return []
        
        required_points = max(self.rsi_period, self.bb_period) + 5
        if len(df) < required_points:
            logger.warning(
                f"{self.name}: Insufficient data points",
                data_points=len(df),
                required=required_points
            )
            return []
        
        symbol = df['symbol'].iloc[0]
        
        # Calculate indicators
        df = self.calculate_rsi(df)
        df = self.calculate_bollinger_bands(df)
        
        # Drop NaN rows
        df = df.dropna(subset=['rsi', 'bb_upper', 'bb_lower'])
        
        if df.empty:
            return []
        
        # Detect anomalies
        anomalies = []
        
        # RSI Overbought (>70) or Oversold (<30)
        df['rsi_overbought'] = df['rsi'] > 70
        df['rsi_oversold'] = df['rsi'] < 30
        
        for _, row in df[df['rsi_overbought'] | df['rsi_oversold']].iterrows():
            condition = 'overbought' if row['rsi_overbought'] else 'oversold'
            score = abs(row['rsi'] - 50) / 20  # Normalize to 0-2.5 range
            
            anomaly = {
                'symbol': symbol,
                'timestamp': row['timestamp'],
                'anomaly_type': f'rsi_{condition}',
                'method': self.name,
                'score': float(score),
                'details': {
                    'rsi': float(row['rsi']),
                    'condition': condition,
                    'close_price': float(row['close']),
                    'indicator': 'RSI'
                }
            }
            anomalies.append(anomaly)
        
        # Bollinger Bands Breach
        df['bb_breach_upper'] = df['close'] > df['bb_upper']
        df['bb_breach_lower'] = df['close'] < df['bb_lower']
        
        for _, row in df[df['bb_breach_upper'] | df['bb_breach_lower']].iterrows():
            breach_type = 'upper' if row['bb_breach_upper'] else 'lower'
            
            # Calculate how far beyond the band
            if breach_type == 'upper':
                distance = (row['close'] - row['bb_upper']) / row['bb_std']
            else:
                distance = (row['bb_lower'] - row['close']) / row['bb_std']
            
            anomaly = {
                'symbol': symbol,
                'timestamp': row['timestamp'],
                'anomaly_type': f'bollinger_breach_{breach_type}',
                'method': self.name,
                'score': float(distance),
                'details': {
                    'close_price': float(row['close']),
                    'bb_upper': float(row['bb_upper']),
                    'bb_lower': float(row['bb_lower']),
                    'bb_middle': float(row['bb_middle']),
                    'breach_type': breach_type,
                    'distance_std': float(distance),
                    'indicator': 'Bollinger Bands'
                }
            }
            anomalies.append(anomaly)
        
        if anomalies:
            logger.info(
                f"Detected {len(anomalies)} technical indicator anomalies for {symbol}",
                symbol=symbol,
                method=self.name,
                count=len(anomalies)
            )
        
        return anomalies