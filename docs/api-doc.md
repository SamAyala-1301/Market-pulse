# MarketPulse API Documentation

This document provides a clear and simple overview of all available API endpoints in the MarketPulse system. It covers health checks, anomaly queries, stock price data, metrics, and usage examples.

---

## Base URL
```
http://localhost:8000
```

---

## Authentication
No authentication is enabled in development mode.
Production deployments should add JWT or similar authentication.

---

## 1. Health Endpoints

### **GET /**
Basic API status.

**Response:**
```json
{
  "service": "MarketPulse API",
  "version": "1.0.0",
  "status": "healthy"
}
```

---

### **GET /health**
Returns API and database health.

**Response:**
```json
{
  "api": "healthy",
  "database": "healthy"
}
```

---

## 2. Anomaly Endpoints

### **GET /anomalies**
Fetch anomalies with optional filtering.

**Query Parameters:**
- `symbol` — filter by stock symbol
- `method` — filter by detection method
- `anomaly_type` — filter by anomaly category
- `days` — lookback window (default: 7)
- `limit` — max results (default: 100)

**Example:**
```bash
curl "http://localhost:8000/anomalies?symbol=AAPL&days=30&limit=50"
```

**Response:**
```json
[
  {
    "id": 123,
    "symbol": "AAPL",
    "timestamp": "2025-11-15T14:30:00",
    "anomaly_type": "price_movement",
    "method": "zscore",
    "score": 3.42,
    "details": {
      "daily_return": -8.5,
      "direction": "drop",
      "close_price": 175.20
    },
    "created_at": "2025-11-16T02:00:00"
  }
]
```

---

### **GET /anomalies/stats**
Aggregate anomaly counts.

**Query Parameters:**
- `days` — period to analyze (default: 30)

**Example:**
```bash
curl "http://localhost:8000/anomalies/stats?days=7"
```

**Response:**
```json
{
  "total_anomalies": 156,
  "by_method": { "zscore": 25, "iqr": 18 },
  "by_symbol": { "AAPL": 18, "GOOGL": 15 },
  "by_type": { "price_movement": 65, "volume_spike": 28 }
}
```

---

## 3. Stock Price Endpoints

### **GET /stocks/{symbol}/latest**
Returns latest price data.

**Example:**
```bash
curl http://localhost:8000/stocks/AAPL/latest
```

**Response:**
```json
{
  "symbol": "AAPL",
  "timestamp": "2025-11-17T16:00:00",
  "open": 175.50,
  "high": 177.20,
  "low": 174.80,
  "close": 176.40,
  "volume": 52000000
}
```

**404 Response:**
```json
{ "detail": "Symbol INVALID not found" }
```

---

### **GET /stocks/{symbol}/history**
Returns recent historical prices.

**Query Parameters:**
- `days` — number of days (default: 30)

**Example:**
```bash
curl "http://localhost:8000/stocks/AAPL/history?days=7"
```

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "timestamp": "2025-11-17T16:00:00",
    "open": 175.50,
    "high": 177.20,
    "low": 174.80,
    "close": 176.40,
    "volume": 52000000
  }
]
```

---

## 4. Metrics

### **GET /metrics**
Prometheus metrics for service monitoring.

**Example:**
```bash
curl http://localhost:8000/metrics
```

**Sample Output:**
```
api_requests_total{endpoint="get_anomalies",status="success"} 145
api_request_duration_seconds_bucket{le="0.1"} 120
```

---

## 5. Error Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 404 | Not found |
| 422 | Invalid parameters |
| 500 | Server error |

---

## 6. Usage Examples

### Python
```python
import requests
BASE_URL = "http://localhost:8000"

anomalies = requests.get(f"{BASE_URL}/anomalies", params={"symbol": "AAPL", "days": 7}).json()
latest = requests.get(f"{BASE_URL}/stocks/AAPL/latest").json()
```

### JavaScript
```javascript
const axios = require('axios');
const BASE_URL = 'http://localhost:8000';

async function fetch() {
  const anomalies = await axios.get(`${BASE_URL}/anomalies?symbol=AAPL`);
  console.log(anomalies.data);
}
```

### cURL
```bash
curl "http://localhost:8000/anomalies?days=1"
curl "http://localhost:8000/stocks/AAPL/history?days=5"
```

---

## 7. Interactive Docs
- Swagger UI → http://localhost:8000/docs
- ReDoc → http://localhost:8000/redoc