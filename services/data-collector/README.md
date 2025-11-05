# Data Collector Service

Fetches stock market data from Yahoo Finance and stores in PostgreSQL.

## Features
- Fetches OHLCV data for configured symbols
- Initial historical data load (365 days)
- Scheduled daily updates
- Upsert logic (no duplicates)
- Prometheus metrics
- Graceful error handling

## Configuration

See `.env.example` for available environment variables.

## Symbols Monitored

- AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META (Tech stocks)
- SPY, QQQ (Market indices)
- ^VIX (Volatility index)

## Metrics

- `data_fetcher_requests_total` - Total fetch requests (by symbol, status)
- `data_fetcher_records_saved_total` - Total records saved
- `data_fetcher_duration_seconds` - Fetch operation duration
- `data_fetcher_last_fetch_timestamp` - Last successful fetch time

## Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (requires running postgres/redis)
python src/main.py
```

## Docker
```bash
# Build
docker build -t marketpulse-data-collector .

# Run
docker run -p 8001:8001 --env-file .env marketpulse-data-collector
```