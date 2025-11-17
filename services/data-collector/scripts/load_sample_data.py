"""Generate realistic sample stock data"""
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime, timedelta

DATABASE_URL = "postgresql://mpuser:mppass123@localhost:5432/marketpulse"

def generate_stock_data(symbol, days=365, initial_price=100):
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    np.random.seed(hash(symbol) % 2**32)
    
    returns = np.random.normal(0.0005, 0.02, days)
    prices = initial_price * np.exp(np.cumsum(returns))
    
    data = []
    for i, date in enumerate(dates):
        close = prices[i]
        daily_range = close * 0.02
        open_price = close + np.random.uniform(-daily_range/2, daily_range/2)
        high = max(open_price, close) + np.random.uniform(0, daily_range)
        low = min(open_price, close) - np.random.uniform(0, daily_range)
        volume = int(np.random.uniform(5e6, 5e7))
        
        data.append({
            'symbol': symbol,
            'timestamp': date.to_pydatetime().replace(tzinfo=None),
            'open': round(float(open_price), 2),
            'high': round(float(high), 2),
            'low': round(float(low), 2),
            'close': round(float(close), 2),
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    
    # Add 10 anomalies per stock
    anomaly_indices = np.random.choice(len(df)-10, size=10, replace=False) + 5
    for idx in anomaly_indices:
    # Bigger moves: ±15-20%
        df.loc[idx, 'close'] *= np.random.choice([0.80, 0.85, 1.15, 1.20])
    
    return df

STOCKS = {
    'AAPL': 170, 'GOOGL': 140, 'MSFT': 370, 'AMZN': 145, 'TSLA': 240,
    'NVDA': 480, 'META': 320, 'SPY': 450, 'QQQ': 380
}

def main():
    print("Loading sample data...")
    engine = create_engine(DATABASE_URL)
    
    for symbol, price in STOCKS.items():
        print(f"Generating {symbol}...")
        df = generate_stock_data(symbol, days=365, initial_price=price)
        df.to_sql('stock_prices', engine, if_exists='append', index=False)
        print(f"✓ {symbol}: {len(df)} records")
    
    print("\n✓ Data loaded successfully!")

if __name__ == "__main__":
    main()
