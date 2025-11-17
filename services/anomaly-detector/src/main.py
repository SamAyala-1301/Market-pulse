import time
import schedule
import structlog
from prometheus_client import start_http_server, Counter, Gauge, Histogram, Info
from database import SessionLocal, test_connection, fetch_stock_data, save_anomalies
from detectors.zscore_detector import ZScoreDetector
from detectors.iqr_detector import IQRDetector
from detectors.isolation_forest_detector import IsolationForestDetector
from detectors.moving_average_detector import MovingAverageDetector
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
detection_counter = Counter(
    'anomaly_detector_detections_total',
    'Total anomalies detected',
    ['symbol', 'method', 'anomaly_type']
)

detection_duration = Histogram(
    'anomaly_detector_duration_seconds',
    'Time spent on anomaly detection',
    ['operation']
)

last_detection_timestamp = Gauge(
    'anomaly_detector_last_run_timestamp',
    'Unix timestamp of last detection run'
)

symbols_processed = Counter(
    'anomaly_detector_symbols_processed_total',
    'Total symbols processed',
    ['status']
)

service_info = Info(
    'anomaly_detector_service',
    'Anomaly detector service information'
)


class AnomalyDetectionService:
    """Main anomaly detection service"""
    
    def __init__(self):
    # Initialize ALL detectors
        self.detectors = [
        ZScoreDetector(threshold=2.5, window=30),  # Lowered threshold
        IQRDetector(multiplier=1.5, window=30),
        IsolationForestDetector(contamination=0.1, n_estimators=100),
        MovingAverageDetector(window=20, threshold_pct=5.0)
    ]
    
        self.running = False
    
    # Set service info
        service_info.info({
        'version': '1.1.0',
        'detectors_count': str(len(self.detectors)),
        'symbols_count': str(len(settings.symbols))
    })
    
        logger.info(
        "Initialized AnomalyDetectionService",
        detectors=[d.name for d in self.detectors],
        symbols_count=len(settings.symbols)
    )
    
    def detect_for_symbol(self, db, symbol: str) -> int:
        """
        Run all detectors for a single symbol
        
        Args:
            db: Database session
            symbol: Stock symbol to analyze
            
        Returns:
            Total number of anomalies detected
        """
        try:
            # Fetch data
            df = fetch_stock_data(db, symbol, days=settings.lookback_days)
            
            if df.empty:
                logger.warning(f"No data available for {symbol}")
                symbols_processed.labels(status='no_data').inc()
                return 0
            
            logger.info(
                f"Processing {symbol}",
                symbol=symbol,
                data_points=len(df),
                date_range=f"{df['timestamp'].min()} to {df['timestamp'].max()}"
            )
            
            # Run all detectors
            all_anomalies = []
            
            for detector in self.detectors:
                try:
                    anomalies = detector.detect(df)
                    
                    # Update metrics
                    for anom in anomalies:
                        detection_counter.labels(
                            symbol=symbol,
                            method=anom['method'],
                            anomaly_type=anom['anomaly_type']
                        ).inc()
                    
                    all_anomalies.extend(anomalies)
                    
                except Exception as e:
                    logger.error(
                        f"Detector {detector.name} failed for {symbol}",
                        detector=detector.name,
                        symbol=symbol,
                        error=str(e)
                    )
            
            # Save anomalies to database
            if all_anomalies:
                save_anomalies(db, all_anomalies)
                logger.info(
                    f"Saved {len(all_anomalies)} anomalies for {symbol}",
                    symbol=symbol,
                    anomalies_count=len(all_anomalies)
                )
            
            symbols_processed.labels(status='success').inc()
            return len(all_anomalies)
            
        except Exception as e:
            logger.error(
                f"Failed to process {symbol}",
                symbol=symbol,
                error=str(e)
            )
            symbols_processed.labels(status='error').inc()
            return 0
    
    def run_detection(self):
        """Run detection for all symbols"""
        logger.info("Starting anomaly detection run")
        
        with detection_duration.labels(operation='full_run').time():
            db = SessionLocal()
            
            try:
                total_anomalies = 0
                
                for symbol in settings.symbols:
                    anomalies_count = self.detect_for_symbol(db, symbol)
                    total_anomalies += anomalies_count
                
                last_detection_timestamp.set_to_current_time()
                
                logger.info(
                    "Detection run completed",
                    total_anomalies=total_anomalies,
                    symbols_processed=len(settings.symbols)
                )
                
            finally:
                db.close()
    
    def start(self):
        """Start the anomaly detection service"""
        logger.info(
            "Starting Anomaly Detection Service",
            symbols_count=len(settings.symbols),
            detectors_count=len(self.detectors),
            metrics_port=settings.metrics_port
        )
        
        # Test database connection
        if not test_connection():
            logger.error("Cannot connect to database, exiting")
            return
        
        # Start Prometheus metrics server
        start_http_server(settings.metrics_port)
        logger.info(f"Metrics server started on port {settings.metrics_port}")
        
        # Run initial detection
        logger.info("Running initial anomaly detection...")
        self.run_detection()
        
        # Schedule detection runs
        # Run daily at 6 PM (after data collection at 5 PM)
        schedule.every().day.at("18:00").do(self.run_detection)
        
        # For testing: also run every 6 hours
        # schedule.every(6).hours.do(self.run_detection)
        
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
    service = AnomalyDetectionService()
    service.start()


if __name__ == "__main__":
    main()