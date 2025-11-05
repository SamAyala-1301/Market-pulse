from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "marketpulse"
    postgres_user: str = "mpuser"
    postgres_password: str = "mppass123"
    
    # Stocks to monitor (10 symbols for Sprint 0)
    symbols: List[str] = [
        "AAPL",   # Apple
        "GOOGL",  # Google
        "MSFT",   # Microsoft
        "AMZN",   # Amazon
        "TSLA",   # Tesla
        "NVDA",   # Nvidia
        "META",   # Meta
        "SPY",    # S&P 500 ETF
        "QQQ",    # Nasdaq ETF
        "^VIX"    # Volatility Index
    ]
    
    # Data collection settings
    fetch_interval_hours: int = 24  # Daily data for now
    historical_days: int = 365      # 1 year of history
    
    # Redis (for future use)
    redis_host: str = "redis"
    redis_port: int = 6379
    
    # Prometheus metrics
    metrics_port: int = 8001
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()