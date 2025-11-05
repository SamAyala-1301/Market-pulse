import time
import schedule
import structlog
from prometheus_client import start_http_server, Counter, Gauge, Histogram, Info
from sqlalchemy.orm import Session
from database import SessionLocal, test_connection, upsert_stock_prices
from fetcher import DataFetcher
from config import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Prometheus metrics
fetch_counter = Counter(
    'data_fetcher_requests_total',
    'Total fetch requests',
    ['symbol', 'status']
)

records_saved = Counter(
    'data_fetcher_records_saved_total',
    'Total records saved to database'
)

fetch_duration = Histogram(
    'data_fetcher_duration_seconds',
    'Time spent fetching data',
    ['operation']
)

last_fetch_timestamp = Gauge(
    'data_fetcher_last_fetch_timestamp',
    'Unix timestamp of last successful fetch'
)

service_info = Info(
    'data_fetcher_service',
    'Data fetcher service information'
)


class DataCollectorService:
    """Main data collection service"""
    
    def __init__(self):
        self.fetcher = DataFetcher(symbols=settings.symbols)
        self.running = False
        
        # Set service info
        service_info.info({
            'version': '1.0.0',
            'symbols_count': str(len(settings.symbols)),
            'fetch_interval_hours': str(settings.fetch_interval_hours)
        })
    
    def fetch_and_store_historical(self):
        """Fetch and store historical data (initial load)"""
        logger.info(
            "Starting historical data fetch",
            symbols_count=len(settings.symbols),
            days=settings.historical_days
        )
        
        with fetch_duration.labels(operation='historical').time():
            # Fetch data for all symbols
            all_data = self.fetcher.fetch_all_symbols(
                days=settings.historical_days
            )
            
            # Store in database
            db = SessionLocal()
            try:
                for symbol, df in all_data.items():
                    try:
                        records = df.to_dict('records')
                        count = upsert_stock_prices(db, records)
                        
                        records_saved.inc(count)
                        fetch_counter.labels(symbol=symbol, status='success').inc()
                        
                        logger.info(
                            f"Saved {count} records for {symbol}",
                            symbol=symbol,
                            records=count
                        )
                        
                    except Exception as e:
                        fetch_counter.labels(symbol=symbol, status='error').inc()
                        logger.error(
                            f"Failed to save data for {symbol}",
                            symbol=symbol,
                            error=str(e)
                        )
                
                last_fetch_timestamp.set_to_current_time()
                logger.info("Historical data fetch completed successfully")
                
            finally:
                db.close()
    
    def fetch_and_store_daily(self):
        """Fetch and store daily update (scheduled job)"""
        logger.info("Starting daily data fetch")
        
        with fetch_duration.labels(operation='daily').time():
            all_data = self.fetcher.fetch_all_symbols(days=5)  # Just last 5 days
            
            db = SessionLocal()
            try:
                total_records = 0
                
                for symbol, df in all_data.items():
                    try:
                        records = df.to_dict('records')
                        count = upsert_stock_prices(db, records)
                        
                        total_records += count
                        records_saved.inc(count)
                        fetch_counter.labels(symbol=symbol, status='success').inc()
                        
                    except Exception as e:
                        fetch_counter.labels(symbol=symbol, status='error').inc()
                        logger.error(
                            f"Failed to save data for {symbol}",
                            symbol=symbol,
                            error=str(e)
                        )
                
                last_fetch_timestamp.set_to_current_time()
                logger.info(
                    "Daily data fetch completed",
                    total_records=total_records
                )
                
            finally:
                db.close()
    
    def start(self):
        """Start the data collection service"""
        logger.info(
            "Starting Data Collector Service",
            symbols=settings.symbols,
            metrics_port=settings.metrics_port
        )
        
        # Test database connection
        if not test_connection():
            logger.error("Cannot connect to database, exiting")
            return
        
        # Start Prometheus metrics server
        start_http_server(settings.metrics_port)
        logger.info(f"Metrics server started on port {settings.metrics_port}")
        
        # Run initial historical data fetch
        logger.info("Running initial historical data fetch...")
        self.fetch_and_store_historical()
        
        # Schedule daily fetches (run at 5 PM ET / 17:00)
        schedule.every().day.at("17:00").do(self.fetch_and_store_daily)
        
        # For testing: also run every 6 hours
        # schedule.every(6).hours.do(self.fetch_and_store_daily)
        
        logger.info("Scheduler started, service is running")
        self.running = True
        
        # Main loop
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Shutting down gracefully...")
            self.running = False


def main():
    """Entry point"""
    service = DataCollectorService()
    service.start()


if __name__ == "__main__":
    main()