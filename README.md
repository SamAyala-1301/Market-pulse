# MarketPulse - Production-Grade Financial Anomaly Detection System

![Python](https://img.shields.io/badge/python-3.11-blue)
![Docker](https://img.shields.io/badge/docker-enabled-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Real-time financial market anomaly detection system using multiple ML and statistical methods. Built with production-grade microservices architecture.

## 🎯 Key Features

- **6 Detection Methods**: Z-score, IQR, Isolation Forest, Moving Average, Volume Anomaly, Technical Indicators
- **9 Financial Instruments**: Tech stocks (AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META) + Market indices (SPY, QQQ)
- **REST API**: FastAPI with full CRUD operations and filtering
- **Real-time Monitoring**: Prometheus metrics + Grafana dashboards
- **Kubernetes Ready**: Helm charts for production deployment
- **Production Infrastructure**: Docker, PostgreSQL, Redis, Grafana, Prometheus

## 📊 Detection Methods

| Method | Type | Sensitivity | Best For |
|--------|------|-------------|----------|
| **Z-Score** | Statistical | High | Sudden price spikes |
| **IQR** | Statistical | Medium | Robust outlier detection |
| **Isolation Forest** | ML | Medium | Multi-variate patterns |
| **Moving Average** | Trend | Medium | Trend breaks |
| **Volume Anomaly** | Statistical | High | Unusual trading activity |
| **Technical Indicators** | Domain | High | RSI extremes, Bollinger breaches |

## 🚀 Quick Start

### Prerequisites
```bash
- Docker & Docker Compose
- 4GB RAM minimum
- Python 3.11+ (for local development)
```

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/market-pulse
cd market-pulse

# Start infrastructure
docker-compose up -d

# Load sample data (since yfinance is blocked)
cd services/data-collector
python scripts/load_sample_data.py

# Verify everything is running
docker-compose ps
```

### Access Services

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Metrics**: 
  - Data Collector: http://localhost:8001/metrics
  - Anomaly Detector: http://localhost:8002/metrics
  - API: http://localhost:8000/metrics

## 📋 API Usage Examples

### Get Recent Anomalies
```bash
curl "http://localhost:8000/anomalies?limit=10"
```

### Filter by Symbol
```bash
curl "http://localhost:8000/anomalies?symbol=AAPL&days=30"
```

### Get Statistics
```bash
curl http://localhost:8000/anomalies/stats
```

### Latest Stock Price
```bash
curl http://localhost:8000/stocks/AAPL/latest
```

### Interactive API Documentation
Visit http://localhost:8000/docs for full Swagger UI

## 🏗️ Architecture
```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Data Collector │────▶│  PostgreSQL  │◀────│ Anomaly Detector│
│   (Synthetic)   │     │              │     │  (6 Methods)    │
└─────────────────┘     └──────────────┘     └─────────────────┘
                               │                      │
                               ▼                      │
                        ┌─────────────┐               │
                        │   FastAPI   │◀──────────────┘
                        │   REST API  │
                        └─────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
   ┌──────────┐         ┌────────────┐        ┌─────────┐
   │  Redis   │         │ Prometheus │        │ Grafana │
   │  Cache   │         │  Metrics   │        │Dashboard│
   └──────────┘         └────────────┘        └─────────┘
```

### Microservices

| Service | Port | Purpose | Tech Stack |
|---------|------|---------|------------|
| **PostgreSQL** | 5432 | Data storage | PostgreSQL 15 |
| **Redis** | 6379 | Caching (future) | Redis 7 |
| **Data Collector** | 8001 | Fetch market data | Python, SQLAlchemy |
| **Anomaly Detector** | 8002 | Run detection algorithms | Python, scikit-learn |
| **API** | 8000 | REST endpoints | FastAPI, Pydantic |
| **Prometheus** | 9090 | Metrics collection | Prometheus |
| **Grafana** | 3000 | Visualization | Grafana |

## 📊 Performance Metrics

### Current Statistics
```bash
# Get live statistics
docker-compose exec postgres psql -U mpuser -d marketpulse -c "
SELECT 
    (SELECT COUNT(*) FROM stock_prices) as total_prices,
    (SELECT COUNT(*) FROM anomalies) as total_anomalies,
    (SELECT COUNT(DISTINCT symbol) FROM stock_prices) as symbols,
    (SELECT COUNT(DISTINCT method) FROM anomalies) as methods;
"
```

**Typical Output:**
- Stock Prices: ~3,285 records (365 days × 9 symbols)
- Anomalies Detected: 800-1,200 (depending on market conditions)
- Detection Methods: 6
- Symbols Monitored: 9

### Detection Performance

| Method | Avg Detections | Avg Score | Processing Time |
|--------|---------------|-----------|-----------------|
| Z-Score | 80-120 | 3.5 | <0.5s |
| IQR | 60-90 | 2.8 | <0.5s |
| Isolation Forest | 100-150 | 6.2 | 1-2s |
| Moving Average | 50-80 | 3.1 | <0.5s |
| Volume Anomaly | 70-100 | 4.2 | <0.5s |
| Technical Indicators | 150-200 | 4.5 | 1s |

## 🔧 Configuration

### Data Collector

Edit `services/data-collector/config.py`:
```python
class Settings(BaseSettings):
    symbols: List[str] = ["AAPL", "GOOGL", "MSFT", ...]
    historical_days: int = 365
    fetch_interval_hours: int = 24
```

### Anomaly Detector

Edit `services/anomaly-detector/config.py`:
```python
class Settings(BaseSettings):
    lookback_days: int = 60
    zscore_threshold: float = 2.5
    rolling_window: int = 30
```

### Detection Thresholds

To adjust sensitivity, modify detector initialization in `services/anomaly-detector/src/main.py`:
```python
self.detectors = [
    ZScoreDetector(threshold=2.5, window=30),     # Lower = more sensitive
    IQRDetector(multiplier=1.5, window=30),       # Lower = more sensitive
    IsolationForest(contamination=0.1),           # Higher = more anomalies
    MovingAverageDetector(threshold_pct=5.0),     # Lower = more sensitive
    VolumeAnomalyDetector(threshold=3.0),
    TechnicalIndicatorsDetector(rsi_period=14)
]
```

## 📈 Database Schema

### stock_prices
```sql
CREATE TABLE stock_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(12, 4),
    high DECIMAL(12, 4),
    low DECIMAL(12, 4),
    close DECIMAL(12, 4),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, timestamp)
);
```

### anomalies
```sql
CREATE TABLE anomalies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    method VARCHAR(50) NOT NULL,
    score DECIMAL(10, 6),
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🚢 Deployment

### Docker Compose (Local/Dev)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Kubernetes (Production)
```bash
# Install with Helm
helm install marketpulse ./helm/marketpulse

# Upgrade
helm upgrade marketpulse ./helm/marketpulse

# Uninstall
helm uninstall marketpulse

# Custom values
helm install marketpulse ./helm/marketpulse -f custom-values.yaml
```

### Environment Variables
```bash
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=marketpulse
POSTGRES_USER=mpuser
POSTGRES_PASSWORD=mppass123

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# API
API_PORT=8000
LOG_LEVEL=INFO
```

## 🧪 Testing

### Run Tests
```bash
# Data collector tests
cd services/data-collector
pytest tests/ -v

# Anomaly detector tests
cd services/anomaly-detector
pytest tests/ -v

# API tests
cd services/api
pytest tests/ -v
```

### Manual Testing
```bash
# Check data collection
docker-compose exec postgres psql -U mpuser -d marketpulse -c "
SELECT symbol, COUNT(*), MIN(timestamp), MAX(timestamp) 
FROM stock_prices GROUP BY symbol;
"

# Check anomaly detection
docker-compose exec postgres psql -U mpuser -d marketpulse -c "
SELECT method, COUNT(*), ROUND(AVG(score::float), 2) 
FROM anomalies GROUP BY method;
"

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/anomalies?limit=5 | jq
```

## 📚 Project Structure
```
market-pulse/
├── services/
│   ├── data-collector/
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── fetcher.py
│   │   │   └── database.py
│   │   ├── scripts/
│   │   │   └── load_sample_data.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── anomaly-detector/
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── database.py
│   │   │   └── detectors/
│   │   │       ├── base.py
│   │   │       ├── zscore_detector.py
│   │   │       ├── iqr_detector.py
│   │   │       ├── isolation_forest_detector.py
│   │   │       ├── moving_average_detector.py
│   │   │       ├── volume_detector.py
│   │   │       └── technical_indicators_detector.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── api/
│       ├── src/
│       │   └── main.py
│       ├── Dockerfile
│       └── requirements.txt
├── infrastructure/
│   ├── postgres/
│   │   └── init.sql
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       └── provisioning/
├── helm/
│   └── marketpulse/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
├── docs/
│   ├── architecture.md
│   ├── api-documentation.md
│   ├── deployment-guide.md
│   └── development-guide.md
├── docker-compose.yml
└── README.md
```

## 🔍 Troubleshooting

### No Anomalies Detected
```bash
# Check if data exists
docker-compose exec postgres psql -U mpuser -d marketpulse -c "SELECT COUNT(*) FROM stock_prices;"

# Check detector logs
docker-compose logs anomaly-detector | grep -i error

# Reload data with more anomalies
cd services/data-collector
python scripts/load_sample_data.py

# Restart detector
docker-compose restart anomaly-detector
```

### API Not Responding
```bash
# Check API logs
docker-compose logs api

# Test database connection
curl http://localhost:8000/health

# Restart API
docker-compose restart api
```

### Grafana No Data
```bash
# Check datasource
# Grafana UI → Configuration → Data Sources → PostgreSQL → Save & Test

# Verify connection from Grafana container
docker-compose exec grafana psql -h postgres -U mpuser -d marketpulse -c "SELECT COUNT(*) FROM anomalies;"

# Check manual panel queries work
# Use simple query: SELECT COUNT(*) FROM anomalies;
```

### Memory Issues
```bash
# Check resource usage
docker stats

# Limit resources in docker-compose.yml
services:
  anomaly-detector:
    deploy:
      resources:
        limits:
          memory: 1G
```

## 🎓 Learning Outcomes

### Technical Skills Demonstrated

- **Data Engineering**: ETL pipelines, time-series data handling
- **Machine Learning**: Anomaly detection, unsupervised learning
- **Backend Development**: REST API design, microservices
- **DevOps**: Docker, Kubernetes, CI/CD concepts
- **Monitoring**: Prometheus metrics, Grafana dashboards
- **Database**: PostgreSQL optimization, schema design
- **System Design**: Scalability, fault tolerance, observability

### ML Concepts Applied

- Statistical outlier detection (Z-score, IQR)
- Ensemble methods (multiple detector consensus)
- Feature engineering (technical indicators)
- Time series analysis
- Multi-variate anomaly detection
- Model evaluation without ground truth

### Production Considerations

- Service health checks
- Metrics and observability
- Error handling and logging
- Resource management
- API rate limiting
- Data validation
- Graceful degradation

## 🚧 Known Limitations

### Current Implementation

1. **Synthetic Data**: Using generated data due to yfinance API blocks
   - **Impact**: Results are realistic but not actual market data
   - **Solution**: Can integrate Alpha Vantage, Polygon.io, or other paid APIs

2. **No Real-time Updates**: Currently batch processing (daily)
   - **Impact**: 24-hour detection lag
   - **Solution**: Sprint 3+ would add streaming with Kafka

3. **Single Instance**: No horizontal scaling yet
   - **Impact**: Limited throughput
   - **Solution**: K8s deployment with multiple replicas

4. **No Alert Routing**: Anomalies detected but not automatically escalated
   - **Impact**: Manual monitoring required
   - **Solution**: Add Slack/email webhooks, PagerDuty integration

5. **No Feedback Loop**: Can't mark false positives
   - **Impact**: No model improvement over time
   - **Solution**: Add feedback API, retrain with labeled data

### Future Enhancements

- **Real Market Data**: Integrate with paid APIs (Alpha Vantage, IEX Cloud)
- **Streaming Architecture**: Kafka + Spark for real-time processing
- **Advanced ML**: LSTM for time series, AutoML for hyperparameter tuning
- **Correlation Analysis**: Cross-symbol anomalies, sector movements
- **News Integration**: Correlate anomalies with news sentiment
- **Mobile App**: React Native app with push notifications
- **Multi-Tenancy**: Support multiple users/portfolios
- **Cloud Deployment**: AWS/GCP/Azure with Terraform IaC

## 📊 Metrics Dashboard

### System Metrics (Prometheus)

- `data_fetcher_requests_total{symbol, status}` - Data fetch attempts
- `data_fetcher_records_saved_total` - Records written to DB
- `anomaly_detector_detections_total{symbol, method, type}` - Anomalies detected
- `anomaly_detector_duration_seconds{operation}` - Detection latency
- `api_requests_total{endpoint, status}` - API request counts
- `api_request_duration_seconds` - API response times

### Business Metrics

- Total anomalies detected
- Detection rate per symbol
- Method effectiveness (precision/recall estimates)
- False positive rate (manual labeling)
- Coverage (% of trading days monitored)

## 🤝 Contributing

This is a portfolio project, but suggestions are welcome!

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Data**: Synthetic data generated based on realistic price movements
- **Inspiration**: Real-world trading anomaly detection systems
- **Tools**: 
  - FastAPI for modern Python APIs
  - scikit-learn for ML algorithms
  - Prometheus & Grafana for observability
  - Docker for containerization

## 📬 Contact

**Your Name** - Sai Sampath Ayalasomayajula (arg5506@gmail.com)

---

⭐ If you found this project helpful, please consider giving it a star!

Built with ❤️ for learning and demonstrating production ML engineering skills.
