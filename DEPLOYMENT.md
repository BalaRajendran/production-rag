# Deployment Guide

Complete guide for deploying the Production RAG Framework to various environments.

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [AWS Deployment](#aws-deployment)
5. [GCP Deployment](#gcp-deployment)
6. [Azure Deployment](#azure-deployment)
7. [Kubernetes Deployment](#kubernetes-deployment)
8. [Serverless Deployment](#serverless-deployment)
9. [Environment Configuration](#environment-configuration)
10. [Security Hardening](#security-hardening)
11. [Monitoring & Logging](#monitoring--logging)
12. [Scaling Strategies](#scaling-strategies)

---

## Pre-Deployment Checklist

### Required Services

- [ ] OpenAI API account with credits
- [ ] Pinecone account (Serverless or Pod-based)
- [ ] Cohere API account
- [ ] Domain name (optional but recommended)
- [ ] SSL certificate (for production)

### Configuration

- [ ] All environment variables set
- [ ] API keys secured in secrets manager
- [ ] Database indexes created
- [ ] Health check endpoints verified
- [ ] CORS settings configured
- [ ] Rate limits defined

### Testing

- [ ] All endpoints tested locally
- [ ] Load testing completed
- [ ] Error handling verified
- [ ] Documentation updated
- [ ] Example queries work

---

## Local Development

### Using Python Directly

```bash
# 1. Install dependencies
uv pip install -e .

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Run server
python main.py

# 4. Verify
curl http://localhost:8000/health
```

### Using uvicorn

```bash
# Development with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Environment Variables

Create `.env` file:
```env
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=rag-index
COHERE_API_KEY=...
```

---

## Docker Deployment

### Build and Run

```bash
# Build image
docker build -t production-rag:latest .

# Run container
docker run -d \
  --name rag-api \
  -p 8000:8000 \
  --env-file .env \
  production-rag:latest

# Check logs
docker logs -f rag-api

# Check health
curl http://localhost:8000/health
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Production Docker Configuration

**Dockerfile.prod:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependencies
COPY pyproject.toml .

# Install production dependencies
RUN uv pip install --system -e .

# Copy application
COPY . .

# Non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run with multiple workers
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## AWS Deployment

### Option 1: Elastic Container Service (ECS)

**1. Build and Push to ECR:**
```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Create repository
aws ecr create-repository --repository-name production-rag

# Build and tag
docker build -t production-rag:latest .
docker tag production-rag:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/production-rag:latest

# Push
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/production-rag:latest
```

**2. Create ECS Task Definition:**
```json
{
  "family": "production-rag",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "rag-api",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/production-rag:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:openai-key"
        },
        {
          "name": "PINECONE_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:pinecone-key"
        },
        {
          "name": "COHERE_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:cohere-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/production-rag",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

**3. Create ECS Service:**
```bash
aws ecs create-service \
  --cluster production-cluster \
  --service-name rag-api \
  --task-definition production-rag \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=rag-api,containerPort=8000"
```

### Option 2: AWS App Runner

```bash
# Create App Runner service from ECR
aws apprunner create-service \
  --service-name production-rag \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/production-rag:latest",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {}
      },
      "ImageRepositoryType": "ECR"
    },
    "AutoDeploymentsEnabled": true
  }' \
  --instance-configuration '{
    "Cpu": "1024",
    "Memory": "2048"
  }'
```

### Option 3: Elastic Beanstalk

**Dockerrun.aws.json:**
```json
{
  "AWSEBDockerrunVersion": "1",
  "Image": {
    "Name": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/production-rag:latest",
    "Update": "true"
  },
  "Ports": [
    {
      "ContainerPort": 8000,
      "HostPort": 8000
    }
  ]
}
```

```bash
# Deploy to Elastic Beanstalk
eb init -p docker production-rag
eb create production-rag-env
eb deploy
```

---

## GCP Deployment

### Cloud Run (Recommended)

```bash
# Build and push to Artifact Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/production-rag

# Deploy to Cloud Run
gcloud run deploy production-rag \
  --image gcr.io/PROJECT_ID/production-rag \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=secretRef:openai-key:latest \
  --set-env-vars PINECONE_API_KEY=secretRef:pinecone-key:latest \
  --set-env-vars COHERE_API_KEY=secretRef:cohere-key:latest \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --min-instances 1 \
  --port 8000
```

### GKE (Google Kubernetes Engine)

See [Kubernetes Deployment](#kubernetes-deployment) section.

---

## Azure Deployment

### Azure Container Apps

```bash
# Create resource group
az group create --name production-rag-rg --location eastus

# Create container registry
az acr create --resource-group production-rag-rg \
  --name productionragacr --sku Basic

# Build and push
az acr build --registry productionragacr \
  --image production-rag:latest .

# Create Container App environment
az containerapp env create \
  --name production-rag-env \
  --resource-group production-rag-rg \
  --location eastus

# Deploy Container App
az containerapp create \
  --name production-rag \
  --resource-group production-rag-rg \
  --environment production-rag-env \
  --image productionragacr.azurecr.io/production-rag:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 10 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --secrets \
    openai-key=secretref:openai-api-key \
    pinecone-key=secretref:pinecone-api-key \
    cohere-key=secretref:cohere-api-key
```

---

## Kubernetes Deployment

### Deployment YAML

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: production-rag
  labels:
    app: production-rag
spec:
  replicas: 3
  selector:
    matchLabels:
      app: production-rag
  template:
    metadata:
      labels:
        app: production-rag
    spec:
      containers:
      - name: rag-api
        image: production-rag:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: openai-api-key
        - name: PINECONE_API_KEY
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: pinecone-api-key
        - name: COHERE_API_KEY
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: cohere-api-key
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: production-rag
spec:
  selector:
    app: production-rag
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: production-rag-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: production-rag
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Deploy:**
```bash
# Create secrets
kubectl create secret generic rag-secrets \
  --from-literal=openai-api-key=$OPENAI_API_KEY \
  --from-literal=pinecone-api-key=$PINECONE_API_KEY \
  --from-literal=cohere-api-key=$COHERE_API_KEY

# Deploy
kubectl apply -f deployment.yaml

# Check status
kubectl get pods
kubectl get svc
```

---

## Serverless Deployment

### AWS Lambda (with Function URLs)

**Note:** Cold starts may be an issue. Consider provisioned concurrency.

```python
# lambda_handler.py
from mangum import Mangum
from main import app

handler = Mangum(app)
```

**Deploy:**
```bash
# Package
pip install mangum -t .
zip -r function.zip .

# Create Lambda function
aws lambda create-function \
  --function-name production-rag \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT:role/lambda-role \
  --handler lambda_handler.handler \
  --zip-file fileb://function.zip \
  --memory-size 2048 \
  --timeout 300 \
  --environment Variables="{OPENAI_API_KEY=$OPENAI_API_KEY,...}"

# Create Function URL
aws lambda create-function-url-config \
  --function-name production-rag \
  --auth-type NONE
```

---

## Environment Configuration

### Production .env Template

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# OpenAI
OPENAI_API_KEY=sk-...

# Pinecone
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=rag-production

# Cohere
COHERE_API_KEY=...

# RAG Configuration
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RETRIEVAL=50
TOP_K_RERANK=15
MAX_QUERIES_GENERATED=5

# Model Configuration
EMBEDDING_MODEL=text-embedding-3-large
LLM_MODEL=gpt-4-turbo-preview

# Monitoring (optional)
SENTRY_DSN=
NEW_RELIC_LICENSE_KEY=
```

### Secrets Management

**AWS Secrets Manager:**
```bash
aws secretsmanager create-secret \
  --name production-rag/api-keys \
  --secret-string file://secrets.json
```

**GCP Secret Manager:**
```bash
gcloud secrets create openai-api-key --data-file=-
```

**Azure Key Vault:**
```bash
az keyvault secret set \
  --vault-name rag-keyvault \
  --name openai-api-key \
  --value "sk-..."
```

---

## Security Hardening

### 1. Add Authentication

```python
# In main.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    # Verify JWT token
    if not is_valid_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials

@app.post("/query")
async def query(
    request: QueryRequest,
    credentials = Depends(verify_token)
):
    # Protected endpoint
    pass
```

### 2. Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/query")
@limiter.limit("10/minute")
async def query(request: Request, query_request: QueryRequest):
    pass
```

### 3. HTTPS Only

```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
```

### 4. Security Headers

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)
```

---

## Monitoring & Logging

### Application Monitoring

```python
# In main.py
import logging
from prometheus_client import Counter, Histogram

# Metrics
query_counter = Counter('rag_queries_total', 'Total queries')
query_duration = Histogram('rag_query_duration_seconds', 'Query duration')

@app.post("/query")
async def query(request: QueryRequest):
    query_counter.inc()
    with query_duration.time():
        response = await rag_service.query(request)
    return response
```

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

@app.post("/query")
async def query(request: QueryRequest):
    logger.info(
        "query_received",
        query=request.query,
        has_history=bool(request.conversation_history)
    )
    response = await rag_service.query(request)
    logger.info(
        "query_completed",
        chunks_retrieved=len(response.chunks),
        query_type=response.query_type
    )
    return response
```

---

## Scaling Strategies

### Horizontal Scaling

```bash
# AWS ECS
aws ecs update-service \
  --cluster production-cluster \
  --service rag-api \
  --desired-count 5

# Kubernetes
kubectl scale deployment production-rag --replicas=5
```

### Auto-Scaling Configuration

**AWS ECS:**
```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/production-cluster/rag-api \
  --min-capacity 2 \
  --max-capacity 10

aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/production-cluster/rag-api \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

### Database Scaling

**Pinecone:**
- Serverless: Auto-scales automatically
- Pod-based: Configure pod size and replicas

---

## Post-Deployment Checklist

- [ ] Health check endpoint responding
- [ ] All API endpoints tested
- [ ] SSL certificate configured
- [ ] Monitoring dashboards set up
- [ ] Log aggregation configured
- [ ] Backup strategy in place
- [ ] Disaster recovery plan documented
- [ ] Performance baselines established
- [ ] Cost monitoring enabled
- [ ] Documentation updated

---

## Rollback Procedure

```bash
# AWS ECS
aws ecs update-service \
  --cluster production-cluster \
  --service rag-api \
  --task-definition production-rag:PREVIOUS_VERSION

# Kubernetes
kubectl rollout undo deployment/production-rag

# Docker
docker stop rag-api
docker rm rag-api
docker run -d --name rag-api production-rag:PREVIOUS_TAG
```

---

## Support & Troubleshooting

For deployment issues, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

For architecture questions, see [ARCHITECTURE.md](ARCHITECTURE.md)
