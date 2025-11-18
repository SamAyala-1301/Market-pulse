from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import os

# Logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mpuser:mppass123@postgres:5432/marketpulse"
)
engine = create_engine(DATABASE_URL)

# Metrics
request_counter = Counter('api_requests_total', 'Total API requests', ['endpoint', 'status'])
request_duration = Histogram('api_request_duration_seconds', 'API request duration')

# FastAPI app
app = FastAPI(
    title="MarketPulse API",
    description="Financial anomaly detection API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Anomaly(BaseModel):
    id: int
    symbol: str
    timestamp: datetime
    anomaly_type: str
    method: str
    score: float
    details: dict
    created_at: datetime

class StockPrice(BaseModel):
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

class AnomalyStats(BaseModel):
    total_anomalies: int
    by_method: dict
    by_symbol: dict
    by_type: dict

# Routes
@app.get("/")
async def root():
    """API health check"""
    request_counter.labels(endpoint='root', status='success').inc()
    return {
        "service": "MarketPulse API",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "api": "healthy",
        "database": db_status
    }

@app.get("/anomalies", response_model=List[Anomaly])
async def get_anomalies(
    symbol: Optional[str] = None,
    method: Optional[str] = None,
    anomaly_type: Optional[str] = None,
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get anomalies with filters"""
    
    with request_duration.time():
        try:
            query = """
                SELECT id, symbol, timestamp, anomaly_type, method, 
                       CAST(score AS FLOAT) as score, details, created_at
                FROM anomalies 
                WHERE timestamp >= NOW() - INTERVAL ':days days'
            """
            params = {"days": days}
            
            if symbol:
                query += " AND symbol = :symbol"
                params["symbol"] = symbol
            
            if method:
                query += " AND method = :method"
                params["method"] = method
            
            if anomaly_type:
                query += " AND anomaly_type = :anomaly_type"
                params["anomaly_type"] = anomaly_type
            
            query += " ORDER BY timestamp DESC LIMIT :limit"
            params["limit"] = limit
            
            with engine.connect() as conn:
                result = conn.execute(text(query), params)
                anomalies = [dict(row._mapping) for row in result]
            
            request_counter.labels(endpoint='get_anomalies', status='success').inc()
            logger.info(f"Retrieved {len(anomalies)} anomalies")
            
            return anomalies
            
        except Exception as e:
            request_counter.labels(endpoint='get_anomalies', status='error').inc()
            logger.error(f"Error retrieving anomalies: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/anomalies/stats", response_model=AnomalyStats)
async def get_anomaly_stats(days: int = Query(30, ge=1, le=365)):
    """Get anomaly statistics"""
    
    try:
        with engine.connect() as conn:
            # Total count
            total_result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM anomalies 
                WHERE timestamp >= NOW() - INTERVAL ':days days'
            """), {"days": days})
            total = total_result.scalar()
            
            # By method
            method_result = conn.execute(text("""
                SELECT method, COUNT(*) as count 
                FROM anomalies 
                WHERE timestamp >= NOW() - INTERVAL ':days days'
                GROUP BY method
            """), {"days": days})
            by_method = {row[0]: row[1] for row in method_result}
            
            # By symbol
            symbol_result = conn.execute(text("""
                SELECT symbol, COUNT(*) as count 
                FROM anomalies 
                WHERE timestamp >= NOW() - INTERVAL ':days days'
                GROUP BY symbol
            """), {"days": days})
            by_symbol = {row[0]: row[1] for row in symbol_result}
            
            # By type
            type_result = conn.execute(text("""
                SELECT anomaly_type, COUNT(*) as count 
                FROM anomalies 
                WHERE timestamp >= NOW() - INTERVAL ':days days'
                GROUP BY anomaly_type
            """), {"days": days})
            by_type = {row[0]: row[1] for row in type_result}
        
        request_counter.labels(endpoint='get_stats', status='success').inc()
        
        return {
            "total_anomalies": total,
            "by_method": by_method,
            "by_symbol": by_symbol,
            "by_type": by_type
        }
        
    except Exception as e:
        request_counter.labels(endpoint='get_stats', status='error').inc()
        logger.error(f"Error retrieving stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stocks/{symbol}/latest")
async def get_latest_price(symbol: str):
    """Get latest stock price"""
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT symbol, timestamp, 
                       CAST(open AS FLOAT) as open,
                       CAST(high AS FLOAT) as high,
                       CAST(low AS FLOAT) as low,
                       CAST(close AS FLOAT) as close,
                       volume
                FROM stock_prices 
                WHERE symbol = :symbol 
                ORDER BY timestamp DESC 
                LIMIT 1
            """), {"symbol": symbol})
            
            row = result.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
            
            request_counter.labels(endpoint='get_latest_price', status='success').inc()
            return dict(row._mapping)
            
    except HTTPException:
        raise
    except Exception as e:
        request_counter.labels(endpoint='get_latest_price', status='error').inc()
        logger.error(f"Error retrieving price: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stocks/{symbol}/history")
async def get_price_history(
    symbol: str,
    days: int = Query(30, ge=1, le=365)
):
    """Get historical stock prices"""
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT symbol, timestamp,
                       CAST(open AS FLOAT) as open,
                       CAST(high AS FLOAT) as high,
                       CAST(low AS FLOAT) as low,
                       CAST(close AS FLOAT) as close,
                       volume
                FROM stock_prices 
                WHERE symbol = :symbol 
                    AND timestamp >= NOW() - INTERVAL ':days days'
                ORDER BY timestamp DESC
            """), {"symbol": symbol, "days": days})
            
            prices = [dict(row._mapping) for row in result]
            
            if not prices:
                raise HTTPException(status_code=404, detail=f"No data for {symbol}")
            
            request_counter.labels(endpoint='get_price_history', status='success').inc()
            return prices
            
    except HTTPException:
        raise
    except Exception as e:
        request_counter.labels(endpoint='get_price_history', status='error').inc()
        logger.error(f"Error retrieving history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)