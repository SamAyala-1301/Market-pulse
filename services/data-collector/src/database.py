from sqlalchemy import create_engine, Column, Integer, String, DateTime, Numeric, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text
from datetime import datetime
import structlog
from config import settings

logger = structlog.get_logger()

# Database URL
DATABASE_URL = (
    f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
)

# SQLAlchemy setup
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class StockPrice(Base):
    """Stock price data model"""
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open = Column(Numeric(12, 4))
    high = Column(Numeric(12, 4))
    low = Column(Numeric(12, 4))
    close = Column(Numeric(12, 4))
    volume = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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


def upsert_stock_prices(db, records: list) -> int:
    """
    Upsert stock prices (insert or update on conflict)
    
    Args:
        db: Database session
        records: List of dictionaries with stock price data
        
    Returns:
        Number of records processed
    """
    try:
        stmt = insert(StockPrice).values(records)
        
        # On conflict (symbol, timestamp), update all fields
        stmt = stmt.on_conflict_do_update(
            index_elements=['symbol', 'timestamp'],
            set_={
                'open': stmt.excluded.open,
                'high': stmt.excluded.high,
                'low': stmt.excluded.low,
                'close': stmt.excluded.close,
                'volume': stmt.excluded.volume,
            }
        )
        
        result = db.execute(stmt)
        db.commit()
        
        return len(records)
        
    except Exception as e:
        db.rollback()
        logger.error("Failed to upsert stock prices", error=str(e))
        raise