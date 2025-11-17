# MarketPulse Architecture

## System Overview

MarketPulse is a microservices-based anomaly detection system for financial markets.

## Components

### 1. Data Collector Service
- **Purpose**: Fetch stock market data from external APIs
- **Technology**: Python, yfinance, SQLAlchemy
- **Schedule**: Daily at 5 PM (after market close)
- **Output**: OHLCV data in PostgreSQL

### 2. Anomaly Detector Service
- **Purpose**: Detect unusual patterns in market data
- **Technology**: Python, pandas, numpy, scikit-learn
- **Schedule**: Daily at 6 PM (after data collection)
- **Methods**: Z-score detection (Sprint 0)
- **Output**: Anomalies in PostgreSQL

### 3. PostgreSQL Database
- **Purpose**: Persistent storage
- **Tables**: stock_prices, anomalies
- **Future**: Migrate to TimescaleDB for better time-series performance

### 4. Redis
- **Purpose**: Caching and pub/sub messaging
- **Current**: Not actively used (Sprint 0)
- **Future**: Cache API responses, real-time updates

### 5. Prometheus
- **Purpose**: Metrics collection
- **Metrics**:
  - Data fetch success/failure rates
  - Detection counts
  - Processing durations
  - Service health

### 6. Grafana
- **Purpose**: Visualization and monitoring
- **Dashboards**:
  - Service overview
  - Stock prices with anomaly overlays
  - Detection performance

## Data Flow
```
1. Market API (Yahoo Finance)
        ↓
2. Data Collector (fetch & transform)
        ↓
3. PostgreSQL (store)
        ↓
4. Anomaly Detector (analyze)
        ↓
5. PostgreSQL (store anomalies)
        ↓
6. Grafana (visualize)
```

## Detection Algorithm (Z-Score)
```python
# For each stock symbol:
1. Fetch last 60 days of price data
2. Calculate daily returns: (today_close - yesterday_close) / yesterday_close * 100
3. Calculate rolling statistics (30-day window):
   - rolling_mean = mean(daily_returns)
   - rolling_std = std(daily_returns)
4. Calculate z-score: (daily_return - rolling_mean) / rolling_std
5. Flag anomaly if |z-score| > 3.0
6. Store anomaly with metadata
```

## Deployment

### Local Development
- Docker Compose for orchestration
- All services in single network
- Persistent volumes for data

### Production (Future)
- Kubernetes for orchestration
- Helm charts for deployment
- Cloud-managed databases
- Horizontal scaling of detector service

## Security Considerations

### Current (Sprint 0)
- Basic authentication for Grafana
- No external access (localhost only)
- Hardcoded credentials (development only)

### Future
- Environment-based secrets management
- TLS/SSL for all connections
- API authentication tokens
- Role-based access control

## Scalability

### Current Capacity
- 10 symbols
- Daily updates
- Single instance per service

### Future Scaling
- 100+ symbols
- Intraday updates (15-min intervals)
- Multiple detector instances
- Distributed task queue
- Read replicas for database

## Monitoring Strategy

### Metrics Collected
- Business metrics: anomalies detected, symbols processed
- Technical metrics: API response times, DB query duration
- Infrastructure metrics: CPU, memory, disk usage

### Alerting (Future)
- Service down alerts
- Anomaly threshold breaches
- Data collection failures
- High false positive rates

## Cost Analysis

### Current (Sprint 0)
- **Total Cost**: $0/month
- Data API: yfinance (free)
- Compute: Local Docker
- Storage: Local volumes

### Future Cloud Deployment
- Estimated: $5-10/month
- Using free tiers where possible
- Optimization for cost efficiency