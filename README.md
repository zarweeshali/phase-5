# Phase V: Advanced Cloud Deployment

**Branch**: `001-phase5-cloud`  
**Status**: In Progress (Phase 1 & 2 Complete)  
**Spec**: [specs/001-phase5-cloud/spec.md](specs/001-phase5-cloud/spec.md)

## Overview

Phase V implements advanced todo application features with event-driven architecture using Kafka and Dapr, deployed to Kubernetes (Minikube locally, AKS/GKE/OKE in cloud).

## Features

### Part A: Advanced Features
- ✅ **Task Management**: Create, update, delete tasks with due dates, priorities, tags
- ✅ **Recurring Tasks**: Daily, weekly, monthly patterns with auto-creation
- ✅ **Reminders**: Automated reminders via Dapr Jobs API
- ✅ **Search & Filter**: Keyword search, filter by priority/tags/status
- ✅ **Sort**: By due date, priority, creation date
- ✅ **Event-Driven Architecture**: Kafka topics for task-events, reminders, task-updates
- ✅ **Dapr Integration**: Pub/Sub, State, Jobs, Secrets, Service Invocation

### Part B: Local Deployment
- Minikube with full Dapr sidecar injection
- Redpanda (Kafka) for local event streaming
- All Dapr components configured

### Part C: Cloud Deployment
- Azure AKS / Google GKE / Oracle OKE support
- Redpanda Cloud for managed Kafka
- GitHub Actions CI/CD pipeline
- Monitoring and logging configuration

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Chat API Pod (FastAPI + MCP)            │  │
│  │  ┌────────────┐  ┌────────────┐                      │  │
│  │  │ FastAPI    │◀─┤ Dapr       │                      │  │
│  │  │ App        │  │ Sidecar    │                      │  │
│  │  └────────────┘  └────────────┘                      │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  DAPR COMPONENTS                      │  │
│  │  kafka-pubsub │ statestore │ kubernetes-secrets      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
    ┌────▼────┐      ┌──────▼──────┐      ┌──────▼──────┐
    │  Kafka  │      │  Neon DB    │      │  K8s        │
    │(Redpanda)│      │(PostgreSQL) │      │  Secrets    │
    └─────────┘      └─────────────┘      └─────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker Desktop
- Minikube
- Dapr CLI
- kubectl

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run Locally (Development)

```bash
# Start with Dapr sidecar
dapr run --app-id todo-backend --app-port 8000 -- uvicorn src.api.main:app --reload
```

### 4. Deploy to Minikube

```bash
# Start Minikube
minikube start

# Initialize Dapr
dapr init -k

# Deploy Kafka (Redpanda)
helm install redpanda redpanda/redpanda --namespace todo-app --create-namespace

# Apply Dapr components
kubectl apply -f k8s/base/dapr-components/

# Deploy application
kubectl apply -k k8s/overlays/minikube/
```

## Project Structure

```
phase-5/
├── src/
│   └── api/
│       ├── db/              # Database connection
│       ├── models/          # SQLModel models
│       ├── routes/          # FastAPI routes
│       ├── services/        # Business logic
│       ├── schemas/         # Pydantic schemas
│       ├── dapr/            # Dapr utilities
│       │   ├── client.py    # Dapr HTTP client
│       │   ├── publisher.py # Pub/Sub publisher
│       │   ├── state.py     # State management
│       │   ├── jobs.py      # Jobs scheduler
│       │   └── secrets.py   # Secrets manager
│       ├── mcp/             # MCP tools
│       ├── consumers/       # Kafka consumers
│       ├── config.py        # Configuration
│       ├── exceptions.py    # Custom exceptions
│       ├── logging_config.py # Logging setup
│       └── main.py          # FastAPI app
├── k8s/
│   ├── base/
│   │   ├── dapr-components/ # Dapr component configs
│   │   ├── migrations/      # Database migrations
│   │   └── kafka/           # Kafka configs
│   └── overlays/
│       ├── minikube/        # Minikube-specific configs
│       └── cloud/           # Cloud-specific configs (AKS/GKE/OKE)
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   └── e2e/
├── specs/
│   └── 001-phase5-cloud/
│       ├── spec.md          # Feature specification
│       ├── plan.md          # Technical plan
│       ├── tasks.md         # Task breakdown (167 tasks)
│       └── checklists/      # Quality checklists
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

## API Endpoints

### Health Checks
- `GET /health` - Basic health check
- `GET /ready` - Readiness check with dependency health
- `GET /live` - Liveness check

### Tasks (Coming in Phase 3)
- `POST /api/tasks` - Create task
- `GET /api/tasks` - List tasks
- `GET /api/tasks/{id}` - Get task
- `PUT /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task
- `POST /api/tasks/{id}/complete` - Complete task

### Search & Filter (Coming in Phase 4)
- `GET /api/tasks/search?q=keyword` - Search tasks
- `GET /api/tasks/filter?priority=high&tag=work` - Filter tasks

## Kafka Topics

| Topic | Producer | Consumers | Purpose |
|-------|----------|-----------|---------|
| `task-events` | Chat API | Audit, Recurring Task | All task CRUD |
| `reminders` | Chat API | Notification | Reminder triggers |
| `task-updates` | Chat API | WebSocket | Real-time sync |

## Dapr Components

| Component | Type | Purpose |
|-----------|------|---------|
| `kafka-pubsub` | pubsub.kafka | Event streaming |
| `statestore` | state.postgresql | Conversation state |
| `kubernetes-secrets` | secretstores.kubernetes | API keys, credentials |

## Configuration

### Environment Variables

See `.env.example` for all required variables:

```bash
# Application
APP_NAME=phase5-todo-app
APP_ENV=development
LOG_LEVEL=INFO

# OpenAI
OPENAI_API_KEY=sk-...

# Database
DATABASE_URL=postgresql://...

# Dapr
DAPR_HTTP_PORT=3500
DAPR_APP_ID=todo-backend

# Kafka/Redpanda
REDPANDA_BROKERS=cluster.cloud.redpanda.com:9092
REDPANDA_USERNAME=...
REDPANDA_PASSWORD=...
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/api --cov-report=html

# Run specific test type
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/
```

## Code Quality

```bash
# Linting
ruff check src/

# Formatting
black src/

# Type checking
mypy src/
```

## Progress

| Phase | Status | Tasks Complete |
|-------|--------|----------------|
| Specification | ✅ Complete | - |
| Plan | ✅ Complete | - |
| Tasks | ✅ Complete | - |
| Phase 1: Setup | ✅ Complete | 5/5 |
| Phase 2: Foundational | ✅ Complete | 13/13 |
| Phase 3: User Story 1 | ⏳ In Progress | 0/22 |
| Phase 4: User Story 2 | ⏳ Pending | 0/16 |
| Phase 5: User Story 3 | ⏳ Pending | 0/16 |
| Phase 6: User Story 4 | ⏳ Pending | 0/8 |
| Phase 7: User Story 5 | ⏳ Pending | 0/9 |
| Phase 8: Dapr Integration | ⏳ Pending | 0/11 |
| Phase 9: Minikube | ⏳ Pending | 0/13 |
| Phase 10: Cloud | ⏳ Pending | 0/13 |
| Phase 11: CI/CD | ⏳ Pending | 0/9 |
| Phase 12: Monitoring | ⏳ Pending | 0/8 |
| Phase 13: Polish | ⏳ Pending | 0/10 |
| **Total** | **In Progress** | **18/167 (11%)** |

## Constitution

This project follows the Phase V Constitution with 10 core principles:

1. **Dapr-First Architecture** - All infrastructure via Dapr APIs
2. **Event-Driven Design** - All state changes publish events
3. **Test-First Development** - TDD mandatory
4. **Kubernetes-Native Deployment** - Dapr sidecar injection
5. **Cloud Portability** - Multi-cloud support
6. **Observability by Default** - Structured logs, metrics, traces
7. **Security First** - Secrets via Dapr only
8. **Performance Budgets** - Measurable targets
9. **Simplicity (YAGNI)** - Start simple
10. **Spec-Driven Development** - No code without tasks

See [.specify/memory/constitution.md](.specify/memory/constitution.md) for details.

## License

MIT

## Contributors

Built using Spec-Driven Development with SpecKit Plus and Claude Code.
