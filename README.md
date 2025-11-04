# MarketPulse - Financial Market Anomaly Detection System

Real-time anomaly detection system for financial markets using multiple ML methods.

## Features
- Multi-method anomaly detection (statistical, ML, time-series)
- Real-time monitoring of 50+ financial instruments
- Production-grade microservices architecture
- Kubernetes-ready deployment
- Comprehensive monitoring with Prometheus + Grafana

## Tech Stack
- **Backend**: Python 3.11, FastAPI
- **Database**: PostgreSQL → TimescaleDB
- **Cache**: Redis
- **Monitoring**: Prometheus, Grafana
- **Orchestration**: Docker, Kubernetes, Helm
- **ML**: scikit-learn, statsmodels, pandas

## Quick Start
```bash
# Clone repository
git clone <your-repo-url>
cd market-pulse

# Start infrastructure
docker-compose up -d

# Access Grafana
open http://localhost:3000
```

## Architecture

[Architecture diagram coming in Sprint 0]

## Project Status

🚧 **Sprint 0** - Foundation & Data Pipeline (Week 1-2)
- [x] Project setup
- [ ] Infrastructure running
- [ ] Data collection service
- [ ] Basic anomaly detection
- [ ] Grafana dashboard

## Documentation
- [Architecture](docs/architecture.md)
- [API Documentation](docs/api-specs.md)
- [Deployment Guide](docs/deployment.md)

## License
MIT