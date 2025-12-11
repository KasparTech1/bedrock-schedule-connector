# Deployment Guide

This guide covers deploying the KAI ERP Connector to various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Monitoring & Observability](#monitoring--observability)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker 24.0+ and Docker Compose 2.0+
- Access to SyteLine 10 CloudSuite environment
- Network connectivity to SyteLine REST API endpoints

## Environment Configuration

### Required Environment Variables

Create a `.env` file with the following variables:

```bash
# SyteLine Connection (Required)
SL10_BASE_URL=https://your-syteline.infor.com
SL10_USERNAME=your_service_account
SL10_PASSWORD=your_secure_password
SL10_CONFIG_NAME=YOUR_CONFIG_TST  # e.g., BEDROCK_TST or BEDROCK_PRD

# API Security (Required for Production)
JWT_SECRET=generate-a-strong-random-secret-key
ENVIRONMENT=production

# CORS Origins (comma-separated, no wildcards in production)
CORS_ORIGINS=https://your-frontend.com,https://admin.your-domain.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_DAY=10000

# Server Configuration
HOST=0.0.0.0
PORT=8100
LOG_LEVEL=INFO
```

### Generating JWT Secret

```bash
# Generate a secure random secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Docker Deployment

### Single Container (Development/Testing)

```bash
# Build the image
docker build -t kai-erp-connector:latest .

# Run the container
docker run -d \
  --name kai-erp-api \
  -p 8100:8100 \
  --env-file .env \
  kai-erp-connector:latest
```

### Docker Compose (Recommended)

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f kai-erp-connector

# Stop services
docker compose down
```

### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  kai-erp-connector:
    image: kai-erp-connector:latest
    restart: always
    ports:
      - "8100:8100"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    env_file:
      - .env.prod
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8100/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

  kai-erp-frontend:
    image: kai-erp-frontend:latest
    restart: always
    ports:
      - "80:80"
    depends_on:
      kai-erp-connector:
        condition: service_healthy
```

```bash
# Deploy to production
docker compose -f docker-compose.prod.yml up -d
```

## Kubernetes Deployment

### Namespace

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: kai-erp
```

### Secret

```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: kai-erp-secrets
  namespace: kai-erp
type: Opaque
stringData:
  SL10_USERNAME: your_username
  SL10_PASSWORD: your_password
  JWT_SECRET: your_jwt_secret
```

### ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kai-erp-config
  namespace: kai-erp
data:
  SL10_BASE_URL: "https://your-syteline.infor.com"
  SL10_CONFIG_NAME: "YOUR_CONFIG_PRD"
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  CORS_ORIGINS: "https://your-frontend.com"
```

### Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kai-erp-connector
  namespace: kai-erp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: kai-erp-connector
  template:
    metadata:
      labels:
        app: kai-erp-connector
    spec:
      containers:
        - name: api
          image: your-registry/kai-erp-connector:latest
          ports:
            - containerPort: 8100
          envFrom:
            - configMapRef:
                name: kai-erp-config
            - secretRef:
                name: kai-erp-secrets
          resources:
            limits:
              cpu: "1"
              memory: "1Gi"
            requests:
              cpu: "250m"
              memory: "256Mi"
          livenessProbe:
            httpGet:
              path: /health
              port: 8100
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 8100
            initialDelaySeconds: 5
            periodSeconds: 5
```

### Service

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: kai-erp-connector
  namespace: kai-erp
spec:
  selector:
    app: kai-erp-connector
  ports:
    - port: 80
      targetPort: 8100
  type: ClusterIP
```

### Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: kai-erp-ingress
  namespace: kai-erp
  annotations:
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
    - hosts:
        - api.your-domain.com
      secretName: tls-secret
  rules:
    - host: api.your-domain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: kai-erp-connector
                port:
                  number: 80
```

### Deploy to Kubernetes

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

## Monitoring & Observability

### Health Check Endpoint

```bash
curl http://localhost:8100/health
```

Response:
```json
{
  "status": "healthy",
  "service": "kai-erp-connector",
  "version": "3.0.0"
}
```

### Structured Logging

Logs are output in JSON format for easy parsing:

```json
{
  "timestamp": "2024-12-01T12:00:00Z",
  "level": "info",
  "event": "request_completed",
  "method": "GET",
  "path": "/bedrock/schedule",
  "status_code": 200,
  "duration_ms": 150
}
```

### Prometheus Metrics (Future)

Metrics endpoint will be available at `/metrics`:

- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency histogram
- `syteline_api_calls_total` - SyteLine API calls
- `syteline_api_duration_seconds` - SyteLine API latency

## Security Considerations

### Production Checklist

- [ ] Set unique `JWT_SECRET` environment variable
- [ ] Configure explicit `CORS_ORIGINS` (no wildcards)
- [ ] Enable HTTPS/TLS termination
- [ ] Set `ENVIRONMENT=production`
- [ ] Use strong service account credentials
- [ ] Enable rate limiting
- [ ] Configure network policies
- [ ] Regular security updates

### Network Security

1. **TLS Termination**: Always use HTTPS in production
2. **Network Policies**: Restrict pod-to-pod communication
3. **Firewall Rules**: Only allow necessary traffic

### Secrets Management

1. Use Kubernetes Secrets or a secrets manager (Vault, AWS Secrets Manager)
2. Never commit secrets to version control
3. Rotate credentials regularly

## Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check logs
docker logs kai-erp-api

# Common causes:
# - Missing environment variables
# - Network connectivity issues
# - Port conflicts
```

#### API Returns 503

```bash
# Service not initialized - check SyteLine connectivity
curl -v $SL10_BASE_URL/IDORequestService/MGRestService.svc

# Check environment variables are set
docker exec kai-erp-api env | grep SL10
```

#### Rate Limit Errors (429)

```bash
# Check rate limit headers
curl -i http://localhost:8100/health

# Increase limits if needed
RATE_LIMIT_PER_MINUTE=120
```

### Debug Mode

Enable debug logging temporarily:

```bash
LOG_LEVEL=DEBUG docker compose up
```

### Health Check Failed

```bash
# Test health endpoint directly
curl http://localhost:8100/health

# Check container status
docker ps -a

# View recent logs
docker logs --tail 50 kai-erp-api
```

## Performance Tuning

### Connection Pooling

The API uses connection pooling by default. Tune for your workload:

```bash
# Maximum concurrent connections to SyteLine
MAX_CONNECTIONS=20

# Connection timeout (seconds)
CONNECTION_TIMEOUT=30
```

### Memory Allocation

For high-volume deployments:

```yaml
resources:
  limits:
    memory: "4Gi"
  requests:
    memory: "1Gi"
```

### Scaling

Horizontal scaling is recommended:

```bash
# Kubernetes
kubectl scale deployment kai-erp-connector --replicas=4

# Docker Compose
docker compose up -d --scale kai-erp-connector=4
```

---

For additional help, see the [CONTRIBUTING.md](../CONTRIBUTING.md) or open an issue on GitHub.
