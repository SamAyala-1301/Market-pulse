from sqlalchemy import create_engine, Column, Integer, String, DateTime, Numeric, JSON, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pandas as pd
import structlog
from config import settings

logger = structlog.get_logger()

DATABASE_URL = (
    f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Anomaly(Base):
    """Anomaly detection results"""
    __tablename__ = "anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    anomaly_type = Column(String(50), nullable=False)
    method = Column(String(50), nullable=False)
    score = Column(Numeric(10, 6))
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def fetch_stock_data(db, symbol: str, days: int = 60) -> pd.DataFrame:
    """
    Fetch recent stock data for analysis
    
    Args:
        db: Database session
        symbol: Stock symbol
        days: Number of days to fetch
        
    Returns:
        DataFrame with columns: symbol, timestamp, open, high, low, close, volume
    """
    query = text("""
        SELECT symbol, timestamp, 
               CAST(open AS FLOAT) as open,
               CAST(high AS FLOAT) as high,
               CAST(low AS FLOAT) as low,
               CAST(close AS FLOAT) as close,
               volume
        FROM stock_prices
        WHERE symbol = :symbol
        ORDER BY timestamp DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {"symbol": symbol, "limit": days})
    df = pd.DataFrame(
        result.fetchall(), 
        columns=['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
    )
    
    # Sort by timestamp ascending for time series analysis
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    return df


def save_anomalies(db, anomalies: list) -> int:
    """
    Save detected anomalies to database
    
    Args:
        db: Database session
        anomalies: List of anomaly dictionaries
        
    Returns:
        Number of anomalies saved
    """
    if not anomalies:
        return 0
    
    try:
        for anom in anomalies:
            db_anomaly = Anomaly(**anom)
            db.add(db_anomaly)
        
        db.commit()
        logger.info(f"Saved {len(anomalies)} anomalies to database")
        return len(anomalies)
        
    except Exception as e:
        db.rollback()
        logger.error("Failed to save anomalies", error=str(e))
        raise


def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        return False