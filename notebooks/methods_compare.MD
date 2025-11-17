# Detection Method Comparison - Sprint 1

## Methods Implemented

| Method | Type | Strengths | Weaknesses | Best For |
|--------|------|-----------|------------|----------|
| **Z-Score** | Statistical | Fast, interpretable | Assumes normal distribution | Sudden price spikes |
| **IQR** | Statistical | Robust to outliers | Less sensitive | General anomalies |
| **Isolation Forest** | ML | Multi-variate, no assumptions | Black box, needs tuning | Complex patterns |
| **Moving Average** | Trend | Simple, intuitive | Lags behind real-time | Trend breaks |

## Results (Sprint 1)

[Run this query and paste results]:
```sql
SELECT 
    method,
    COUNT(*) as detections,
    ROUND(AVG(score)::numeric, 2) as avg_score,
    ROUND(MIN(score)::numeric, 2) as min_score,
    ROUND(MAX(score)::numeric, 2) as max_score
FROM anomalies 
GROUP BY method;
```

## Observations

1. **Z-Score** (threshold 2.5): Catches [X] anomalies
   - More sensitive than before (was 3.0)
   - Good for statistical outliers

2. **IQR**: Catches [X] anomalies
   - More robust than Z-score
   - Less false positives

3. **Isolation Forest**: Catches [X] anomalies
   - ML-based, considers multiple features
   - Can detect subtle patterns

4. **Moving Average**: Catches [X] anomalies
   - Trend-following
   - Good for sustained deviations

## Method Overlap

[Check how many anomalies are caught by multiple methods]

## Recommendations

- Use ensemble: Flag only if 2+ methods agree
- Different methods for different use cases
- Tune thresholds based on false positive rate