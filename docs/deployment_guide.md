# MarketPulse Deployment Guide

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Compose Production](#docker-compose-production)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Cloud Providers](#cloud-providers)
5. [Monitoring & Logging](#monitoring--logging)
6. [Backup & Recovery](#backup--recovery)
7. [Security Hardening](#security-hardening)

---

## Local Development

### Prerequisites
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Setup
```bash
# Clone repository
git clone https://github.com/yourusername/market-pulse
cd market-pulse

# Start services
docker-compose up -d

# Load sample data
cd services/data-collector
pip install -r requirements.txt
python scripts/load_sample_data.py

# Verify
curl http://localhost:8000/health
```

### Development Workflow
```bash
# View logs
docker-compose logs -f [service-name]

# Rebuild service after code changes
docker-compose build [service-name]
docker-compose up -d [service-name]

# Stop all services
docker-compose down

# Clean everything (including volumes)
docker-compose down -v
```

---

## Docker Compose Production

### Production Configuration

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  redis:
    image: redis:7-alpine
    restart: always
    deploy:
      resources:
        limits:
          memory: 512M

  data-collector:
    build: ./services/data-collector
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      LOG_LEVEL: INFO
    depends_on:
      - postgres
    restart: always

  anomaly-detector:
    build: ./services/anomaly-detector
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    depends_on:
      - postgres
    restart: always

  api:
    build: ./services/api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
    depends_on:
      - postgres
    restart: always

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./infrastructure/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    restart: always

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
    restart: always

volumes:
  postgres_data:
  prometheus_data:
  grafana_data:
```

### Environment Variables

Create `.env.prod`:
```bash
# Database
POSTGRES_DB=marketpulse
POSTGRES_USER=mpuser
POSTGRES_PASSWORD=<strong-password>

# Grafana
GRAFANA_PASSWORD=<strong-password>

# API
API_SECRET_KEY=<random-secret-key>

# Monitoring
ENVIRONMENT=production
```

### Deploy
```bash
# Load environment
export $(cat .env.prod | xargs)

# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## Kubernetes Deployment

### Prerequisites
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify
kubectl version --client
helm version
```

### Local Kubernetes (minikube)
```bash
# Install minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Start cluster
minikube start --cpus 4 --memory 8192

# Enable ingress
minikube addons enable ingress

# Deploy with Helm
helm install marketpulse ./helm/marketpulse

# Check deployment
kubectl get pods
kubectl get services

# Port forward to access locally
kubectl port-forward svc/marketpulse-api 8000:8000
kubectl port-forward svc/marketpulse-grafana 3000:3000
```

### Production Kubernetes

#### 1. Build and Push Images
```bash
# Build images
docker build -t yourdockerhub/marketpulse-data-collector:1.0.0 ./services/data-collector
docker build -t yourdockerhub/marketpulse-anomaly-detector:1.0.0 ./services/anomaly-detector
docker build -t yourdockerhub/marketpulse-api:1.0.0 ./services/api

# Push to registry
docker push yourdockerhub/marketpulse-data-collector:1.0.0
docker push yourdockerhub/marketpulse-anomaly-detector:1.0.0
docker push yourdockerhub/marketpulse-api:1.0.0
```

#### 2. Create Secrets
```bash
# Create namespace
kubectl create namespace marketpulse

# Create database secret
kubectl create secret generic postgres-secret \
  --from-literal=username=mpuser \
  --from-literal=password=<strong-password> \
  --from-literal=database=marketpulse \
  -n marketpulse
```

#### 3. Deploy with Helm
```bash
# Install
helm install marketpulse ./helm/marketpulse \
  --namespace marketpulse \
  --values production-values.yaml

# Upgrade
helm upgrade marketpulse ./helm/marketpulse \
  --namespace marketpulse \
  --values production-values.yaml

# Rollback if needed
helm rollback marketpulse -n marketpulse
```

#### 4. Verify Deployment
```bash
# Check pods
kubectl get pods -n marketpulse

# Check services
kubectl get svc -n marketpulse

# Check logs
kubectl logs -f deployment/marketpulse-api -n marketpulse

# Describe pod for troubleshooting
kubectl describe pod <pod-name> -n marketpulse
```

---

## Cloud Providers

### AWS (EKS)
```bash
# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Create cluster
eksctl create cluster \
  --name marketpulse \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3

# Deploy
helm install marketpulse ./helm/marketpulse \
  --set image.repository=<your-ecr-repo> \
  --set postgres.storageClass=gp2

# Setup ingress with ALB
kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json
```

### GCP (GKE)
```bash
# Create cluster
gcloud container clusters create marketpulse \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-2

# Get credentials
gcloud container clusters get-credentials marketpulse --zone us-central1-a

# Deploy
helm install marketpulse ./helm/marketpulse \
  --set image.repository=gcr.io/<project-id>/marketpulse \
  --set postgres.storageClass=standard-rwo
```

### Azure (AKS)
```bash
# Create resource group
az group create --name marketpulse-rg --location eastus

# Create cluster
az aks create \
  --resource-group marketpulse-rg \
  --name marketpulse \
  --node-count 3 \
  --node-vm-size Standard_D2s_v3

# Get credentials
az aks get-credentials --resource-group marketpulse-rg --name marketpulse

# Deploy
helm install marketpulse ./helm/marketpulse \
  --set image.repository=<your-acr>.azurecr.io/marketpulse
```

---

## Monitoring & Logging

### Prometheus Setup
```bash
# Add Prometheus Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/prometheus \
  --namespace monitoring \
  --create-namespace

# Port forward
kubectl port-forward -n monitoring svc/prometheus-server 9090:80
```

### Grafana Dashboards
```bash
# Import dashboards via API
curl -X POST http://admin:admin@localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @infrastructure/grafana/dashboards/marketpulse-sprint1.json
```

### Centralized Logging (ELK Stack)
```bash
# Install Elasticsearch
helm install elasticsearch elastic/elasticsearch \
  --namespace logging \
  --create-namespace

# Install Kibana
helm install kibana elastic/kibana \
  --namespace logging

# Install Filebeat for log collection
kubectl apply -f infrastructure/logging/filebeat-daemonset.yaml
```

---

## Backup & Recovery

### Database Backup
```bash
# Manual backup
docker-compose exec postgres pg_dump -U mpuser marketpulse > backup_$(date +%Y%m%d).sql

# Automated backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T postgres pg_dump -U mpuser marketpulse | gzip > "$BACKUP_DIR/marketpulse_$DATE.sql.gz"
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
EOF

chmod +x backup.sh

# Add to crontab (daily at 2 AM)
0 2 * * * /path/to/backup.sh
```

### Restore Database
```bash
# From backup file
gunzip -c backup_20251117.sql.gz | docker-compose exec -T postgres psql -U mpuser -d marketpulse

# From Kubernetes
kubectl exec -it postgres-pod -n marketpulse -- psql -U mpuser -d marketpulse < backup.sql
```

### Kubernetes Volume Snapshots
```bash
# Create VolumeSnapshot
kubectl apply -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-snapshot
  namespace: marketpulse
spec:
  volumeSnapshotClassName: csi-hostpath-snapclass
  source:
    persistentVolumeClaimName: postgres-pvc
EOF

# List snapshots
kubectl get volumesnapshots -n marketpulse
```

---

## Security Hardening

### 1. Use Secrets Management
```bash
# Kubernetes secrets
kubectl create secret generic db-credentials \
  --from-literal=username=mpuser \
  --from-literal=password=$(openssl rand -base64 32)

# Or use external secret managers
# AWS Secrets Manager, HashiCorp Vault, etc.
```

### 2. Enable TLS/SSL
```bash
# Generate certificates (Let's Encrypt with cert-manager)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create certificate issuer
kubectl apply -f infrastructure/k8s/cert-issuer.yaml

# Update ingress for TLS
kubectl apply -f infrastructure/k8s/ingress-tls.yaml
```

### 3. Network Policies
```yaml
# Allow only necessary traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
spec:
  podSelector:
    matchLabels:
      app: marketpulse-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

### 4. Resource Limits

Already configured in `helm/marketpulse/values.yaml`:
```yaml
resources:
  limits:
    cpu: 1000m
    memory: 2Gi
  requests:
    cpu: 250m
    memory: 512Mi
```

### 5. Security Scanning
```bash
# Scan Docker images
docker scan marketpulse-api:latest

# Use Trivy
trivy image marketpulse-api:latest

# Add to CI/CD pipeline
```

---

## Troubleshooting

### Common Issues

**Pods CrashLooping:**
```bash
kubectl logs <pod-name> -n marketpulse
kubectl describe pod <pod-name> -n marketpulse
```

**Database Connection Issues:**
```bash
kubectl exec -it <api-pod> -n marketpulse -- env | grep DATABASE
kubectl exec -it <postgres-pod> -n marketpulse -- psql -U mpuser -d marketpulse -c "SELECT 1"
```

**Service Not Accessible:**
```bash
kubectl get svc -n marketpulse
kubectl get ingress -n marketpulse
kubectl port-forward svc/marketpulse-api 8000:8000 -n marketpulse
```

### Health Checks
```bash
# API health
curl http://<external-ip>:8000/health

# Database health
docker-compose exec postgres pg_isready -U mpuser

# Prometheus targets
curl http://localhost:9090/api/v1/targets
```

---

## Performance Tuning

### Database Optimization
```sql
-- Add indexes
CREATE INDEX CONCURRENTLY idx_anomalies_timestamp ON anomalies(timestamp DESC);
CREATE INDEX CONCURRENTLY idx_anomalies_symbol_method ON anomalies(symbol, method);

-- Vacuum analyze
VACUUM ANALYZE stock_prices;
VACUUM ANALYZE anomalies;

-- Adjust PostgreSQL settings
ALTER SYSTEM SET shared_buffers = '1GB';
ALTER SYSTEM SET effective_cache_size = '3GB';
ALTER SYSTEM SET work_mem = '64MB';
```

### Application Tuning
```python
# Increase database connection pool
engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=40)

# Enable caching
@lru_cache(maxsize=128)
def get_anomaly_stats(days: int):
    # cached function
    pass
```

---

## Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Security scan completed
- [ ] Secrets configured
- [ ] Resource limits set
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Documentation updated

### Post-Deployment

- [ ] Health checks passing
- [ ] Metrics flowing to Prometheus
- [ ] Grafana dashboards accessible
- [ ] API responding correctly
- [ ] Database connections stable
- [ ] Logs being collected
- [ ] Alerts configured

---

## Support

For deployment issues:
1. Check logs: `kubectl logs -f <pod-name>`
2. Review documentation
3. Open GitHub issue
