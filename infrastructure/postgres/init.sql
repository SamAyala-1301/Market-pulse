-- Stock prices table
CREATE TABLE IF NOT EXISTS stock_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(12, 4),
    high DECIMAL(12, 4),
    low DECIMAL(12, 4),
    close DECIMAL(12, 4),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_symbol_timestamp_unique ON stock_prices(symbol, timestamp);
CREATE INDEX idx_symbol ON stock_prices(symbol);
CREATE INDEX idx_timestamp ON stock_prices(timestamp DESC);

-- Anomalies table
CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    method VARCHAR(50) NOT NULL,
    score DECIMAL(10, 6),
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_anomalies_symbol ON anomalies(symbol);
CREATE INDEX idx_anomalies_timestamp ON anomalies(timestamp DESC);
CREATE INDEX idx_anomalies_type ON anomalies(anomaly_type);
CREATE INDEX idx_anomalies_method ON anomalies(method);

-- View for daily returns
CREATE OR REPLACE VIEW daily_returns AS
SELECT 
    symbol,
    timestamp,
    close,
    LAG(close) OVER (PARTITION BY symbol ORDER BY timestamp) as prev_close,
    CASE 
        WHEN LAG(close) OVER (PARTITION BY symbol ORDER BY timestamp) IS NOT NULL 
        THEN ((close - LAG(close) OVER (PARTITION BY symbol ORDER BY timestamp)) / 
              LAG(close) OVER (PARTITION BY symbol ORDER BY timestamp) * 100)
        ELSE NULL
    END as daily_return_pct
FROM stock_prices
ORDER BY symbol, timestamp DESC;

-- Seed metadata
CREATE TABLE IF NOT EXISTS system_metadata (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO system_metadata (key, value) VALUES 
    ('schema_version', '1.0'),
    ('initialized_at', NOW()::TEXT);