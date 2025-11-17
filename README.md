# MarketPulse - Financial Market Anomaly Detection System

Production-grade anomaly detection system for financial markets using multiple ML methods and real-time monitoring.


## 🎯 Features

- **Real-time Anomaly Detection**: Z-score based detection on daily returns
- **10 Instruments Monitored**: AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, SPY, QQQ, VIX
- **365 Days Historical Data**: Automatic data collection and storage
- **Microservices Architecture**: Data collector, anomaly detector, API (coming)
- **Production Monitoring**: Prometheus metrics + Grafana dashboards
- **Kubernetes Ready**: Helm charts and containerized services

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 4GB RAM minimum
- Internet connection (for market data APIs)

### Setup
```bash
# Clone repository
git clone 
cd market-pulse

# Start all services
docker-compose up -d

# Wait for data collection (initial load takes 2-3 minutes)
docker-compose logs -f data-collector

# Access Grafana dashboards
open http://localhost:3000
# Login: admin / admin
```

### Verify Installation
```bash
# Check services are running
docker-compose ps

# Check stock data
docker-compose exec postgres psql -U mpuser -d marketpulse -c "SELECT symbol, COUNT(*) FROM stock_prices GROUP BY symbol;"

# Check anomalies
docker-compose exec postgres psql -U mpuser -d marketpulse -c "SELECT COUNT(*) FROM anomalies;"

# Check Prometheus metrics
curl http://localhost:8001  # Data collector metrics
curl http://localhost:8002  # Anomaly detector metrics
```

## 📊 Dashboards

- **Grafana**: http://localhost:3000
  - MarketPulse Overview (service health, metrics)
  - Stock Prices & Anomalies (visualizations)
  
- **Prometheus**: http://localhost:9090
  - Raw metrics and queries

## 🏗️ Architecture
```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Data Collector │────▶│  PostgreSQL  │◀────│ Anomaly Detector│
│   (yfinance)    │     │              │     │   (Z-Score)     │
└─────────────────┘     └──────────────┘     └─────────────────┘
        │                       │                      │
        ▼                       ▼                      ▼
   ┌──────────────────────────────────────────────────────┐
   │              Prometheus + Grafana                     │
   └──────────────────────────────────────────────────────┘
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5432 | Stock prices & anomalies storage |
| Redis | 6379 | Caching (future use) |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Visualization dashboards |
| Data Collector | 8001 | Fetches market data, exposes metrics |
| Anomaly Detector | 8002 | Detects anomalies, exposes metrics |

## 🔧 Configuration

### Data Collector
See `services/data-collector/config.py`:
- `symbols`: List of stock tickers to monitor
- `historical_days`: Days of historical data to fetch (default: 365)
- `fetch_interval_hours`: Update frequency (default: 24)

### Anomaly Detector
See `services/anomaly-detector/config.py`:
- `zscore_threshold`: Anomaly threshold (default: 3.0)
- `rolling_window`: Window for statistics (default: 30 days)
- `lookback_days`: Days of data to analyze (default: 60)

## 📈 Current Anomaly Detection Methods

### Z-Score Method
- Detects unusual daily returns (price movements)
- Flags when |z-score| > 3.0 (configurable)
- Uses 30-day rolling window for mean/std calculation
- Captures both sudden spikes and drops

**Example Detection:**
```
Symbol: TSLA
Date: 2024-10-25
Daily Return: -8.5%
Z-Score: 3.42
Classification: Anomaly (unusual drop)
```

## 🧪 Development

### Project Structure
```
market-pulse/
├── services/
│   ├── data-collector/      # Market data fetching service
│   ├── anomaly-detector/    # Anomaly detection service
│   └── api/                 # REST API (Sprint 3)
├── infrastructure/
│   ├── postgres/            # Database init scripts
│   ├── prometheus/          # Prometheus config
│   └── grafana/             # Grafana dashboards
├── helm/                    # Kubernetes charts
├── docs/                    # Documentation
└── docker-compose.yml       # Local development setup
```

### Running Tests
```bash
# Data collector tests
cd services/data-collector
pytest tests/

# Anomaly detector tests
cd services/anomaly-detector
pytest tests/
```

### Adding New Symbols
Edit `services/data-collector/config.py` and `services/anomaly-detector/config.py`:
```python
symbols = [
    "AAPL", "GOOGL",  # Add your symbols here
    "YOUR_SYMBOL"
]
```
Then restart services:
```bash
docker-compose restart data-collector anomaly-detector
```

## 📊 Data Schema

### stock_prices
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| symbol | VARCHAR(10) | Stock ticker |
| timestamp | TIMESTAMP | Date of price data |
| open/high/low/close | DECIMAL | OHLC prices |
| volume | BIGINT | Trading volume |

### anomalies
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| symbol | VARCHAR(10) | Stock ticker |
| timestamp | TIMESTAMP | Anomaly date |
| anomaly_type | VARCHAR(50) | Type (e.g., "price_movement") |
| method | VARCHAR(50) | Detection method (e.g., "zscore") |
| score | DECIMAL | Anomaly score |
| details | JSONB | Additional metadata |

## 🎯 Roadmap

### ✅ Sprint 0 (Week 1-2) - COMPLETED
- [x] Docker infrastructure
- [x] Data collection from yfinance
- [x] PostgreSQL storage
- [x] Z-score anomaly detection
- [x] Grafana dashboards
- [x] Prometheus monitoring

### 🚧 Sprint 1 (Week 3-4) - NEXT
- [ ] IQR detection method
- [ ] Isolation Forest method
- [ ] Moving average deviation
- [ ] Comparison analysis
- [ ] Enhanced dashboards

### 📋 Sprint 2 (Week 5-6)
- [ ] Volume anomalies
- [ ] Volatility tracking
- [ ] Technical indicators (RSI, MACD)
- [ ] Correlation analysis
- [ ] Multi-dimensional scoring

### 📋 Sprint 3 (Week 7-8)
- [ ] FastAPI service
- [ ] Real-time detection
- [ ] Alert system (Slack/Email)
- [ ] WebSocket updates
- [ ] API documentation

## 🐛 Troubleshooting

### Services won't start
```bash
# Check Docker resources
docker system df

# Clean up and restart
docker-compose down -v
docker-compose up -d
```

### No data in database
```bash
# Check data collector logs
docker-compose logs data-collector

# Manually trigger fetch
docker-compose exec data-collector python src/main.py
```

### Grafana shows no data
- Verify datasources are configured: Configuration → Data Sources
- Check PostgreSQL connection
- Verify data exists in database

## 📝 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- Market data: [yfinance](https://github.com/ranaroussi/yfinance)
- Monitoring: Prometheus & Grafana
- Database: PostgreSQL

## 📬 Contact

Created by [Sai Sampath Ayalasomayajula]

Project Link: [https://github.com/SamAyala-1301/market-pulse](https://github.com/yourusername/market-pulse)