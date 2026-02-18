# Implementation Plan: Phase V - Advanced Cloud Deployment

**Branch**: `001-phase5-cloud` | **Date**: 2026-02-18 | **Spec**: [specs/001-phase5-cloud/spec.md](../../specs/001-phase5-cloud/spec.md)
**Input**: Feature specification for advanced todo app with Kafka event-driven architecture, Dapr integration, and cloud deployment

## Summary

Implement advanced todo application features (recurring tasks, due dates, reminders, priorities, tags, search, filter, sort) with event-driven architecture using Kafka and Dapr. Deploy first to Minikube locally with full Dapr sidecar injection, then to production cloud Kubernetes (Azure AKS / Google GKE / Oracle OKE) with managed Kafka (Redpanda Cloud). Include GitHub Actions CI/CD pipeline and monitoring/logging configuration.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, httpx (Dapr client), kafka-python (via Dapr), sqlmodel/PostgreSQL
**Storage**: Neon DB (PostgreSQL), Dapr State API abstraction
**Testing**: pytest, integration tests with Minikube
**Target Platform**: Kubernetes (Minikube local, AKS/GKE/OKE cloud)
**Project Type**: Backend API with chat interface (MCP tools)
**Performance Goals**: 
- Task event publishing < 100ms (p95)
- Reminder delivery within 1 minute of scheduled time (p99)
- Search/filter results < 500ms for 10k tasks
- Real-time sync propagation < 2 seconds
**Constraints**: 
- Dapr sidecar pattern for all infrastructure interactions
- No direct Kafka client code in application layer
- Kubernetes-native deployment only
**Scale/Scope**: 100 concurrent users, 10k tasks per user

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         KUBERNETES CLUSTER                               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Chat API Pod (FastAPI + MCP)                  │  │
│  │  ┌──────────────┐  ┌──────────────┐                              │  │
│  │  │  FastAPI App │◀─┤ Dapr Sidecar │                              │  │
│  │  │  + MCP Tools │  │  (daprd)     │                              │  │
│  │  └──────────────┘  └──────────────┘                              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              Notification Service Pod (Optional)                 │  │
│  │  ┌──────────────┐  ┌──────────────┐                              │  │
│  │  │ Notif Service│◀─┤ Dapr Sidecar │                              │  │
│  │  └──────────────┘  └──────────────┘                              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              Recurring Task Service Pod (Optional)               │  │
│  │  ┌──────────────┐  ┌──────────────┐                              │  │
│  │  │ Recur Service│◀─┤ Dapr Sidecar │                              │  │
│  │  └──────────────┘  └──────────────┘                              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      DAPR COMPONENTS                              │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │  │
│  │  │ kafka-pubsub    │  │ statestore      │  │ k8s-secrets     │   │  │
│  │  │ (pubsub.kafka)  │  │ (state.postgres)│  │ (secretstores)  │   │  │
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘   │  │
│  └───────────┼────────────────────┼────────────────────┼────────────┘  │
│              │                    │                    │               │
└──────────────┼────────────────────┼────────────────────┼───────────────┘
               │                    │                    │
    ┌──────────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐
    │  Kafka Cluster    │  │  Neon DB       │  │  K8s Secrets   │
    │  (Redpanda Cloud  │  │  (PostgreSQL)  │  │  (API keys)    │
    │   or Strimzi)     │  │                │  │                │
    └───────────────────┘  └────────────────┘  └────────────────┘
```

### Dapr Components Configuration

**1. Kafka Pub/Sub Component** (`kafka-pubsub`):
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: kafka-pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: "kafka-broker:9092"  # Redpanda Cloud or Strimzi
  - name: consumerGroup
    value: "todo-service"
  - name: authType
    value: "saslPlain"  # For Redpanda Cloud
  - name: saslUsername
    secretKeyRef:
      name: kafka-credentials
      key: username
  - name: saslPassword
    secretKeyRef:
      name: kafka-credentials
      key: password
```

**2. PostgreSQL State Store** (`statestore`):
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.postgresql
  version: v1
  metadata:
  - name: connectionString
    secretKeyRef:
      name: neon-db-connection
      key: connectionString
```

**3. Kubernetes Secrets Store** (`kubernetes-secrets`):
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: kubernetes-secrets
spec:
  type: secretstores.kubernetes
  version: v1
```

**4. Dapr Jobs API** (Built-in scheduler):
- Used for scheduling reminders at exact times
- No component configuration needed (built into Dapr)

### Kafka Topics

| Topic | Producer | Consumers | Purpose |
|-------|----------|-----------|---------|
| `task-events` | Chat API (MCP Tools) | Recurring Task Service, Audit Service | All task CRUD operations |
| `reminders` | Chat API (when due date set) | Notification Service | Scheduled reminder triggers |
| `task-updates` | Chat API | WebSocket Service (if implemented) | Real-time client sync |

### Event Schemas

**Task Event**:
```json
{
  "event_type": "created|updated|completed|deleted",
  "task_id": 123,
  "task_data": { /* full task object */ },
  "user_id": "user-abc",
  "timestamp": "2026-02-18T10:30:00Z"
}
```

**Reminder Event**:
```json
{
  "task_id": 123,
  "title": "Submit report",
  "due_at": "2026-02-18T17:00:00Z",
  "remind_at": "2026-02-18T16:30:00Z",
  "user_id": "user-abc"
}
```

## API Design (Dapr-mediated)

### Publishing Events via Dapr Pub/Sub

```python
# Instead of direct Kafka client
import httpx

DAPR_URL = "http://localhost:3500/v1.0"

async def publish_task_event(event_type: str, task_data: dict, user_id: str):
    """Publish task event via Dapr Pub/Sub."""
    event = {
        "event_type": event_type,
        "task_id": task_data["id"],
        "task_data": task_data,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{DAPR_URL}/publish/kafka-pubsub/task-events",
            json=event
        )
```

### Scheduling Reminders via Dapr Jobs API

```python
async def schedule_reminder(task_id: int, remind_at: datetime, user_id: str):
    """Schedule reminder using Dapr Jobs API."""
    job_data = {
        "dueTime": remind_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data": {
            "task_id": task_id,
            "user_id": user_id,
            "type": "reminder"
        }
    }
    
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{DAPR_URL}/v1.0-alpha1/jobs/reminder-task-{task_id}",
            json=job_data
        )
```

### Handling Job Callbacks

```python
@app.post("/api/jobs/trigger")
async def handle_job_trigger(request: Request):
    """Dapr calls this endpoint at scheduled time."""
    job_data = await request.json()
    
    if job_data["data"]["type"] == "reminder":
        # Publish to notification service via Dapr Pub/Sub
        await publish_reminder_event(job_data["data"])
    
    return {"status": "SUCCESS"}
```

### State Management via Dapr

```python
async def save_conversation_state(conv_id: str, messages: list):
    """Save conversation state via Dapr State API."""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{DAPR_URL}/v1.0/state/statestore",
            json=[{
                "key": f"conversation-{conv_id}",
                "value": {"messages": messages}
            }]
        )

async def get_conversation_state(conv_id: str) -> dict:
    """Retrieve conversation state via Dapr State API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{DAPR_URL}/v1.0/state/statestore/conversation-{conv_id}"
        )
        return response.json()
```

### Service Invocation via Dapr

```python
# Frontend calls backend via Dapr Service Invocation
# Frontend: fetch("http://localhost:3500/v1.0/invoke/backend-service/method/api/chat", {...})

# Backend-to-backend (if multiple services)
async def call_notification_service(user_id: str, message: str):
    """Call notification service via Dapr Service Invocation."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{DAPR_URL}/v1.0/invoke/notification-service/method/api/notify",
            json={"user_id": user_id, "message": message}
        )
        return response.json()
```

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Library-First**: Each service (Chat API, Notification, Recurring Task) is self-contained
- [x] **CLI Interface**: All services expose health checks and admin endpoints via CLI
- [x] **Test-First**: TDD mandatory for all features
- [x] **Integration Testing**: Contract tests for Dapr components, inter-service communication
- [x] **Observability**: Structured logging, Dapr built-in metrics
- [x] **Simplicity**: Dapr abstracts complexity, YAGNI principles applied

## Project Structure

### Documentation (this feature)

```text
specs/001-phase5-cloud/
├── spec.md              # Feature specification
├── plan.md              # This technical plan
├── tasks.md             # Task breakdown (from /sp.tasks)
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── research.md          # Technical research (Kafka, Dapr, K8s)
```

### Source Code (repository root)

```text
src/
├── api/
│   ├── routes/
│   │   ├── tasks.py          # Task CRUD endpoints
│   │   ├── chat.py           # MCP chat interface
│   │   └── jobs.py           # Dapr Jobs callback handler
│   ├── models/
│   │   ├── task.py           # Task data model
│   │   ├── event.py          # Event schemas
│   │   └── reminder.py       # Reminder model
│   ├── services/
│   │   ├── task_service.py   # Task business logic
│   │   ├── event_publisher.py # Dapr Pub/Sub publisher
│   │   └── reminder_scheduler.py # Dapr Jobs scheduler
│   └── mcp/
│       └── tools.py          # MCP tool definitions
├── dapr/
│   ├── components/
│   │   ├── kafka-pubsub.yaml
│   │   ├── statestore.yaml
│   │   └── k8s-secrets.yaml
│   └── configurations/
│       └── appconfig.yaml
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
```

### Kubernetes Deployment

```text
k8s/
├── base/
│   ├── namespace.yaml
│   ├── chat-api-deployment.yaml
│   ├── chat-api-service.yaml
│   └── dapr-components/
├── overlays/
│   ├── minikube/
│   │   ├── kustomization.yaml
│   │   └── patches/
│   └── cloud/
│       ├── aks/
│       │   └── kustomization.yaml
│       ├── gke/
│       │   └── kustomization.yaml
│       └── oke/
│           └── kustomization.yaml
└── kafka/
    ├── strimzi-operator.yaml
    └── kafka-cluster.yaml
```

### CI/CD

```text
.github/
└── workflows/
    ├── build-and-test.yaml
    ├── deploy-minikube.yaml
    └── deploy-cloud.yaml
```

**Structure Decision**: Single project with modular source structure. Kubernetes manifests organized by environment (minikube vs cloud) using Kustomize for configuration management.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Dapr sidecar pattern | Required by Phase V spec | Direct Kafka/DB coupling violates cloud-native principles |
| Kubernetes deployment | Required by Phase V spec | Simpler deployments don't demonstrate cloud-native skills |
| Event-driven architecture | Required for advanced features | Synchronous processing can't support recurring tasks, reminders, real-time sync efficiently |

## Deployment Strategy

### Local Development (Minikube)

1. Start Minikube: `minikube start`
2. Install Dapr: `dapr init -k`
3. Deploy Kafka (Redpanda): `helm install redpanda redpanda/redpanda`
4. Apply Dapr components: `kubectl apply -f k8s/base/dapr-components/`
5. Deploy application: `kubectl apply -k k8s/overlays/minikube/`

### Cloud Deployment (Azure AKS Example)

1. Create AKS cluster via Azure CLI
2. Configure kubectl: `az aks get-credentials --resource-group <rg> --name <cluster>`
3. Install Dapr: `dapr init -k`
4. Create Redpanda Cloud cluster and get credentials
5. Create K8s secrets for Kafka credentials
6. Apply Dapr components with cloud-specific configs
7. Deploy application: `kubectl apply -k k8s/overlays/cloud/aks/`

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Kafka connectivity issues | High | Use Dapr Pub/Sub abstraction, retry policies, fallback to local queue |
| Dapr sidecar injection failures | High | Validate Dapr installation, use annotations correctly |
| Cloud provider complexity | Medium | Start with Minikube, use Kustomize for environment-specific configs |
| Reminder timing accuracy | Medium | Use Dapr Jobs API (exact timing) instead of cron polling |
| CI/CD pipeline complexity | Medium | Build incrementally: build → test → deploy to minikube → deploy to cloud |

## Definition of Done

- [ ] All advanced features implemented (recurring tasks, due dates, reminders, priorities, tags, search, filter, sort)
- [ ] Event-driven architecture with Kafka functional
- [ ] All Dapr components working (Pub/Sub, State, Jobs, Secrets, Service Invocation)
- [ ] Minikube deployment successful with full Dapr
- [ ] Cloud deployment successful (AKS/GKE/OKE)
- [ ] GitHub Actions CI/CD pipeline operational
- [ ] Monitoring and logging configured
- [ ] All tests passing (unit, integration, contract)
- [ ] Documentation complete (README, deployment guides)
- [ ] Demo video recorded (90 seconds max)
