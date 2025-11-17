from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "marketpulse"
    postgres_user: str = "mpuser"
    postgres_password: str = "mppass123"
    
    # Detection settings
    lookback_days: int = 60  # How many days of data to analyze
    zscore_threshold: float = 3.0  # Z-score threshold for anomaly
    rolling_window: int = 30  # Rolling window for mean/std calculation
    
    # Symbols (should match data-collector)
    symbols: List[str] = [
        "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA",
        "NVDA", "META", "SPY", "QQQ", "^VIX"
    ]
    
    # Prometheus
    metrics_port: int = 8002
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()