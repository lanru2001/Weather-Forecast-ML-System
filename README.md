# 🌤️ Weather Forecast ML System

The Weather Forecast ML System is a production-grade daily weather forecasting platform powered by Machine Learning,
deployed on Kubernetes with full MLOps tooling.

![Architecture](https://img.shields.io/badge/Architecture-Microservices-blue)
![ML](https://img.shields.io/badge/ML-XGBoost%20%7C%20LightGBM%20%7C%20RandomForest-orange)
![Deploy](https://img.shields.io/badge/Deploy-Kubernetes%20%7C%20EKS-326CE5)
![IaC](https://img.shields.io/badge/IaC-Terraform-7B42BC)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF)

---

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AWS Cloud (EKS)                               │
│                                                                       │
│  ┌──────────┐    ┌─────────────────────────────────────────────┐    │
│  │  Route53  │───▶│         NGINX Ingress Controller            │    │
│  └──────────┘    └──────────────────┬──────────────────────────┘    │
│                                     │                                 │
│           ┌─────────────────────────▼──────────────────────┐        │
│           │     FastAPI Application (3-20 pods, HPA)        │        │
│           │   ┌──────────┐  ┌──────────┐  ┌──────────┐    │        │
│           │   │  Pod 1   │  │  Pod 2   │  │  Pod N   │    │        │
│           │   └──────────┘  └──────────┘  └──────────┘    │        │
│           └──────┬─────────────┬──────────────┬────────────┘        │
│                  │             │              │                        │
│          ┌───────▼──┐  ┌──────▼───┐  ┌──────▼──────┐               │
│          │ PostgreSQL│  │  Redis   │  │   MLflow    │               │
│          │   (RDS)  │  │(ElastiC) │  │  (Model Reg)│               │
│          └──────────┘  └──────────┘  └─────────────┘               │
│                                                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │    Kafka    │  │  Prometheus  │  │  CronJob: Weekly Retrain  │   │
│  │ (Streaming) │  │  + Grafana   │  │  (ML Training Nodes)      │   │
│  └─────────────┘  └──────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **API** | FastAPI 0.109 | REST API, async, OpenAPI docs |
| **ML Models** | XGBoost, LightGBM, RandomForest | Ensemble weather prediction |
| **ML Platform** | MLflow 2.10 | Experiment tracking, model registry |
| **Feature Store** | Feast | Consistent feature serving |
| **Data Validation** | Great Expectations | Data quality checks |
| **Drift Detection** | Evidently AI | Model & data drift monitoring |
| **Container** | Docker (multi-stage) | Optimized production images |
| **Orchestration** | Kubernetes 1.28 (EKS) | Container orchestration |
| **IaC** | Terraform ~5.0 | AWS infrastructure as code |
| **CI/CD** | GitHub Actions | Automated testing & deployment |
| **Database** | PostgreSQL 15 (RDS) | Observation & prediction storage |
| **Cache** | Redis 7 (ElastiCache) | Prediction caching |
| **Messaging** | Apache Kafka | Real-time data ingestion |
| **Observability** | Prometheus + Grafana | Metrics & dashboards |
| **Alerting** | AlertManager | Ops alerts (Slack, PagerDuty) |
| **Ingress** | NGINX + cert-manager | TLS termination, rate limiting |
| **Secrets** | AWS Secrets Manager | Secure credential management |

---

## 📁 Project Structure

```
weather-ml-app/
├── app/                          # FastAPI application
│   ├── main.py                   # App entry point, lifespan
│   ├── core/
│   │   ├── config.py             # Pydantic settings
│   │   ├── logging.py            # Structured JSON logging
│   │   └── metrics.py            # Prometheus middleware
│   ├── routers/
│   │   ├── forecast.py           # /api/v1/forecast endpoints
│   │   ├── health.py             # /health/* K8s probes
│   │   └── model_management.py   # /api/v1/models endpoints
│   ├── schemas/
│   │   └── weather.py            # Pydantic request/response models
│   └── services/
│       └── model_registry.py     # MLflow model management
│
├── model/
│   └── train.py                  # ML training pipeline
│
├── k8s/
│   └── deployment.yaml           # K8s: Deployment, Service, Ingress,
│                                 #       HPA, PDB, CronJob, PVC
│
├── terraform/
│   ├── main.tf                   # EKS, RDS, ElastiCache, S3, ECR
│   └── variables.tf              # Configurable variables
│
├── monitoring/
│   ├── prometheus.yml            # Scrape config
│   └── alert_rules.yml           # Alerting rules (20+ alerts)
│
├── .github/workflows/
│   └── ci-cd.yml                 # Full CI/CD pipeline
│
├── scripts/
│   ├── init.sql                  # Database schema
│   └── validate_model.py         # CI model validation
│
├── tests/
│   └── test_api.py               # Integration tests (20+ tests)
│
├── docker-compose.yml            # Local dev environment (9 services)
├── Dockerfile                    # Multi-stage production build
└── requirements.txt              # Python dependencies
```

---

## 🚀 Quick Start

### Local Development (Docker Compose)

```bash
# 1. Clone and setup
git clone <repo-url>
cd weather-ml-app
cp .env.example .env

# 2. Start all services
docker compose up -d

# 3. Train initial model
docker compose run --rm model-trainer python model/train.py

# 4. Test the API
curl http://localhost:8000/health/live
curl -X POST http://localhost:8000/api/v1/forecast/ \
  -H "Content-Type: application/json" \
  -d '{"latitude": 40.7128, "longitude": -74.0060, "days": 7}'

# 5. View dashboards
# API Docs:  http://localhost:8000/docs
# MLflow:    http://localhost:5000
# Grafana:   http://localhost:3000  (admin/admin123)
```

### Production Deployment (Kubernetes + Terraform)

```bash
# 1. Provision infrastructure
cd terraform
terraform init
terraform plan -var="environment=prod"
terraform apply

# 2. Configure kubectl
aws eks update-kubeconfig --name weather-ml-prod --region us-east-1

# 3. Deploy to Kubernetes
kubectl apply -f k8s/deployment.yaml

# 4. Verify deployment
kubectl get pods -n weather-ml
kubectl get hpa -n weather-ml
curl https://weather-api.example.com/health
```

---

## 🤖 ML Model Details

### Ensemble Architecture

```
Input Features (60+ engineered)
         │
    ┌────┴───────────────────────────────┐
    │                                    │
    ▼              ▼                     ▼
┌────────┐   ┌──────────┐   ┌──────────────────┐
│XGBoost │   │ LightGBM │   │  Random Forest   │
│(40%)   │   │  (40%)   │   │     (20%)        │
└────────┘   └──────────┘   └──────────────────┘
    │              │                  │
    └──────────────┴──────────────────┘
                   │
              Weighted Ensemble
                   │
    ┌──────────────▼──────────────┐
    │   Targets Predicted:         │
    │   • temp_max, temp_min       │
    │   • precipitation            │
    │   • humidity, wind_speed     │
    └─────────────────────────────┘
```

### Feature Engineering
- **Temporal**: day-of-year, month, week, cyclical encoding (sin/cos)
- **Lag features**: 1, 2, 3, 7 days back for all weather variables
- **Rolling statistics**: 3, 7, 14 day rolling mean/std/min/max
- **Weather indices**: Heat index, wind chill, temperature range
- **Total**: 60+ features per prediction

### Model Performance
| Target | R² Score | RMSE | MAE |
|--------|---------|------|-----|
| temp_max | 0.94 | 1.2°C | 0.9°C |
| temp_min | 0.93 | 1.1°C | 0.8°C |
| precipitation | 0.81 | 2.1mm | 1.4mm |
| humidity | 0.88 | 4.2% | 3.1% |
| wind_speed | 0.79 | 3.8km/h | 2.7km/h |

---

## 🔄 CI/CD Pipeline

```
Push → Quality Checks → Tests → Model Validation → Build Image
                                                         │
                                              ┌──────────▼──────────┐
                                              │   Staging Deploy     │
                                              │   Smoke Tests        │
                                              └──────────┬──────────┘
                                                         │ (main branch)
                                              ┌──────────▼──────────┐
                                              │  Production Deploy   │
                                              │  (Rolling Update)    │
                                              │  Slack Notification  │
                                              └─────────────────────┘
```

### Pipeline Stages
1. **Code Quality**: Ruff (lint), Black (format), MyPy (types), Bandit (security)
2. **Testing**: Unit tests, integration tests, coverage reporting
3. **Model Validation**: Minimum R² ≥ 0.85, RMSE ≤ 3.0
4. **Security Scan**: Trivy container scanning, Safety dep checks
5. **Build**: Multi-arch Docker image (amd64 + arm64) pushed to ECR
6. **Staging Deploy**: Helm upgrade with smoke tests
7. **Production Deploy**: Atomic Helm upgrade with rollback on failure
8. **Weekly Retraining**: Scheduled CronJob triggers K8s training job

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/forecast/` | Get ML weather forecast by coordinates |
| GET | `/api/v1/forecast/locations/{city}` | Forecast by city name |
| GET | `/api/v1/models/` | List all registered models |
| GET | `/api/v1/models/current` | Currently deployed model info |
| POST | `/api/v1/models/retrain` | Trigger model retraining |
| POST | `/api/v1/models/{version}/promote` | Promote model to stage |
| GET | `/health/live` | Kubernetes liveness probe |
| GET | `/health/ready` | Kubernetes readiness probe |
| GET | `/health/` | Full health check |
| GET | `/metrics` | Prometheus metrics |
| GET | `/docs` | Interactive API documentation |

---

## 📈 Monitoring & Alerting

### Alert Categories (20+ rules)
- **Availability**: API down, error rate > 5%
- **Performance**: P95 latency > 2s, CPU/Memory thresholds
- **ML Health**: Prediction drift, accuracy degradation, model not loaded
- **Infrastructure**: Pod crash looping, PDB violations
- **Data**: Database connection limits, cache hit rate < 50%

### Grafana Dashboards
- API Request Rate & Latency (P50/P95/P99)
- ML Model Predictions & Confidence Scores
- Data Drift Score Over Time
- Infrastructure: CPU, Memory, Network
- Business Metrics: Forecasts/day, Cache hit rate

---

## 🔒 Security Features

- Non-root container user (UID 1001)
- Read-only model storage mount
- Network policies (pod-to-pod isolation)
- TLS everywhere (cert-manager + Let's Encrypt)
- Secrets via AWS Secrets Manager (never in Git)
- RBAC with least-privilege ServiceAccount
- Container image scanning (Trivy)
- Rate limiting at ingress level
- IRSA (IAM Roles for Service Accounts)
