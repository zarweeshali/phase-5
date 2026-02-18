# Tasks: Phase V - Advanced Cloud Deployment

**Input**: Design documents from `/specs/001-phase5-cloud/` (spec.md, plan.md)
**Prerequisites**: spec.md (required), plan.md (required)
**Branch**: `001-phase5-cloud`

**Tests**: Tests are included for critical integration points and Dapr components.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create project structure: src/api/, src/api/routes/, src/api/models/, src/api/services/, src/api/mcp/, src/dapr/components/, src/dapr/configurations/, k8s/, tests/
- [ ] T002 [P] Initialize Python project with dependencies: fastapi, uvicorn, httpx, sqlmodel, psycopg2-binary, kafka-python (via Dapr only), pytest, python-dotenv
- [ ] T003 [P] Configure linting (ruff/flake8), formatting (black), and mypy type checking
- [ ] T004 [P] Create .env.example with placeholders: DATABASE_URL, OPENAI_API_KEY, REDPANDA_BROKERS, REDPANDA_USERNAME, REDPANDA_PASSWORD, DAPR_HTTP_PORT
- [ ] T005 [P] Create requirements.txt with all dependencies pinned to specific versions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 [P] Create database connection module: src/api/db/connection.py with async PostgreSQL connection using sqlmodel
- [ ] T007 [P] Create base model class: src/api/models/base.py with common fields (id, created_at, updated_at, user_id)
- [ ] T008 [P] Implement Dapr client wrapper: src/api/dapr/client.py with DAPR_URL constant and httpx session management
- [ ] T009 [P] Create Dapr Pub/Sub publisher utility: src/api/dapr/publisher.py with publish_event(topic, data) function
- [ ] T010 [P] Create Dapr State management utility: src/api/dapr/state.py with save_state(key, value) and get_state(key) functions
- [ ] T011 [P] Create Dapr Jobs scheduler utility: src/api/dapr/jobs.py with schedule_job(job_id, due_time, data) function
- [ ] T012 [P] Create Dapr Secrets utility: src/api/dapr/secrets.py with get_secret(secret_name, key) function
- [ ] T013 [P] Setup error handling infrastructure: src/api/exceptions.py with custom exceptions (TaskNotFoundError, ReminderError, KafkaPublishError)
- [ ] T014 [P] Configure structured logging: src/api/logging_config.py with JSON logging format and correlation ID support
- [ ] T015 [P] Create FastAPI app factory: src/api/main.py with lifespan context manager for DB connection
- [ ] T016 [P] Create health check endpoint: src/api/routes/health.py with /health and /ready endpoints
- [ ] T017 [P] Create Dapr components configuration: k8s/base/dapr-components/kafka-pubsub.yaml, statestore.yaml, kubernetes-secrets.yaml
- [ ] T018 [P] Create Dapr application configuration: k8s/base/dapr-components/appconfig.yaml with tracing and metrics enabled

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Create and Manage Tasks with Advanced Features (Priority: P1) 🎯 MVP

**Goal**: Implement core task management with due dates, priorities, tags, recurring patterns

**Independent Test**: User can create a task with all advanced features via chat interface

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T019 [P] [US1] Contract test for task creation endpoint in tests/contract/test_task_api.py
- [ ] T020 [P] [US1] Integration test for task CRUD operations in tests/integration/test_task_service.py
- [ ] T021 [P] [US1] Test Dapr Pub/Sub event publishing in tests/integration/test_event_publisher.py

### Implementation for User Story 1

- [ ] T022 [P] [US1] Create Task model: src/api/models/task.py with fields: id, title, description, due_date, priority (enum: high/medium/low), tags (array), recurring_pattern (JSON), status (enum: pending/completed), user_id, timestamps
- [ ] T023 [P] [US1] Create Priority enum: src/api/models/priority.py with HIGH, MEDIUM, LOW values
- [ ] T024 [P] [US1] Create TaskStatus enum: src/api/models/task_status.py with PENDING, COMPLETED values
- [ ] T025 [P] [US1] Create RecurringPattern model: src/api/models/recurring_pattern.py with pattern_type (enum: daily/weekly/monthly/custom), interval, end_date (optional)
- [ ] T026 [US1] Create Tag model: src/api/models/tag.py with name, color (optional), user_id
- [ ] T027 [US1] Implement TaskService: src/api/services/task_service.py with create_task, get_task, update_task, delete_task, list_tasks methods
- [ ] T028 [US1] Implement task creation with event publishing: src/api/services/task_service.py#create_task publishes "created" event via Dapr Pub/Sub
- [ ] T029 [US1] Implement task update with event publishing: src/api/services/task_service.py#update_task publishes "updated" event via Dapr Pub/Sub
- [ ] T030 [US1] Implement task completion with event publishing: src/api/services/task_service.py#complete_task publishes "completed" event via Dapr Pub/Sub
- [ ] T031 [US1] Implement task deletion with event publishing: src/api/services/task_service.py#delete_task publishes "deleted" event via Dapr Pub/Sub
- [ ] T032 [US1] Create task request/response schemas: src/api/schemas/task.py with TaskCreate, TaskUpdate, TaskResponse Pydantic models
- [ ] T033 [US1] Implement task CRUD endpoints: src/api/routes/tasks.py with POST /tasks, GET /tasks/{id}, PUT /tasks/{id}, DELETE /tasks/{id}, GET /tasks
- [ ] T034 [US1] Add validation for task creation: title required, priority must be valid enum, due_date must be valid ISO8601
- [ ] T035 [US1] Add validation for recurring pattern: pattern_type required, interval must be positive integer
- [ ] T036 [US1] Create MCP tool for task creation: src/api/mcp/tools.py#create_task tool with natural language parsing
- [ ] T037 [US1] Create MCP tool for task update: src/api/mcp/tools.py#update_task tool
- [ ] T038 [US1] Create MCP tool for task completion: src/api/mcp/tools.py#complete_task tool
- [ ] T039 [US1] Create MCP tool for task deletion: src/api/mcp/tools.py#delete_task tool
- [ ] T040 [US1] Add logging for all task operations with correlation IDs
- [ ] T041 [US1] Create database migration for tasks table: k8s/base/migrations/001_create_tasks.sql
- [ ] T042 [US1] Create database migration for tags table: k8s/base/migrations/002_create_tags.sql
- [ ] T043 [US1] Create database migration for task_tags junction table: k8s/base/migrations/003_create_task_tags.sql

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Search, Filter, and Sort Tasks (Priority: P2)

**Goal**: Implement search, filter, and sort functionality for tasks

**Independent Test**: User can search by keyword, filter by priority/tags/status, sort by various criteria

### Tests for User Story 2 ⚠️

- [ ] T044 [P] [US2] Contract test for search endpoint in tests/contract/test_search_api.py
- [ ] T045 [P] [US2] Integration test for filter operations in tests/integration/test_task_filters.py
- [ ] T046 [P] [US2] Test search functionality with various keywords in tests/integration/test_task_search.py

### Implementation for User Story 2

- [ ] T047 [P] [US2] Create task query schema: src/api/schemas/task_query.py with TaskFilter, TaskSort, TaskSearch Pydantic models
- [ ] T048 [US2] Implement TaskQueryService: src/api/services/task_query_service.py with search_tasks, filter_tasks, sort_tasks methods
- [ ] T049 [US2] Implement keyword search: src/api/services/task_query_service.py#search_tasks searches title and description using SQL ILIKE
- [ ] T050 [US2] Implement priority filter: src/api/services/task_query_service.py#filter_tasks filters by priority enum
- [ ] T051 [US2] Implement tags filter: src/api/services/task_query_service.py#filter_tasks filters by tag name using JOIN
- [ ] T052 [US2] Implement status filter: src/api/services/task_query_service.py#filter_tasks filters by task status
- [ ] T053 [US2] Implement due date range filter: src/api/services/task_query_service.py#filter_tasks filters by due_date BETWEEN
- [ ] T054 [US2] Implement sort by due date: src/api/services/task_query_service.py#sort_tasks ORDER BY due_date ASC/DESC
- [ ] T055 [US2] Implement sort by priority: src/api/services/task_query_service.py#sort_tasks with custom priority ordering (HIGH=1, MEDIUM=2, LOW=3)
- [ ] T056 [US2] Implement sort by creation date: src/api/services/task_query_service.py#sort_tasks ORDER BY created_at
- [ ] T057 [US2] Implement combined query: src/api/services/task_query_service.py#query_tasks combines search + filter + sort with pagination
- [ ] T058 [US2] Create search/filter endpoint: src/api/routes/tasks.py#GET /tasks/search with query parameters
- [ ] T059 [US2] Create MCP tool for task search: src/api/mcp/tools.py#search_tasks tool with natural language parsing
- [ ] T060 [US2] Create MCP tool for task filter: src/api/mcp/tools.py#filter_tasks tool
- [ ] T061 [US2] Add query performance logging with execution time tracking
- [ ] T062 [US2] Create database index for search: k8s/base/migrations/004_create_task_search_indexes.sql (indexes on title, description, priority, status, due_date)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Receive Automated Reminders (Priority: P1) 🎯 MVP

**Goal**: Implement automated reminder system using Dapr Jobs API and Kafka event-driven architecture

**Independent Test**: Reminders are scheduled when tasks with due dates are created and fire at the correct time

### Tests for User Story 3 ⚠️

- [ ] T063 [P] [US3] Contract test for reminder scheduling in tests/contract/test_reminder_api.py
- [ ] T064 [P] [US3] Integration test for Dapr Jobs API in tests/integration/test_dapr_jobs.py
- [ ] T065 [P] [US3] Test reminder event publishing to Kafka in tests/integration/test_reminder_pubsub.py
- [ ] T066 [P] [US3] Test end-to-end reminder flow (create task → schedule reminder → receive notification) in tests/e2e/test_reminder_flow.py

### Implementation for User Story 3

- [ ] T067 [P] [US3] Create Reminder model: src/api/models/reminder.py with fields: id, task_id, title, due_at, remind_at, user_id, status (enum: pending/sent/cancelled)
- [ ] T068 [P] [US3] Create ReminderStatus enum: src/api/models/reminder_status.py with PENDING, SENT, CANCELLED values
- [ ] T069 [US3] Create ReminderEvent schema: src/api/schemas/reminder.py with ReminderEvent Pydantic model matching event schema
- [ ] T070 [US3] Implement ReminderScheduler: src/api/services/reminder_scheduler.py with schedule_reminder, cancel_reminder, reschedule_reminder methods
- [ ] T071 [US3] Implement schedule_reminder using Dapr Jobs API: src/api/services/reminder_scheduler.py#schedule_reminder calls Dapr Jobs endpoint with exact dueTime
- [ ] T072 [US3] Implement reminder event publishing: src/api/services/reminder_scheduler.py publishes to "reminders" topic via Dapr Pub/Sub when job fires
- [ ] T073 [US3] Create Dapr Jobs callback endpoint: src/api/routes/jobs.py#POST /api/jobs/trigger to handle job callbacks from Dapr
- [ ] T074 [US3] Implement job callback handler: src/api/services/job_handler.py#handle_reminder_job publishes reminder event to Kafka
- [ ] T075 [US3] Integrate reminder scheduling with task creation: src/api/services/task_service.py#create_task calls ReminderScheduler when due_date is present
- [ ] T076 [US3] Implement reminder cancellation on task deletion: src/api/services/task_service.py#delete_task cancels associated reminders via Dapr Jobs API
- [ ] T077 [US3] Create NotificationService stub: src/api/services/notification_service.py with send_notification method (for future implementation)
- [ ] T078 [US3] Implement notification event consumer: src/api/consumers/reminder_consumer.py consumes from "reminders" topic and calls NotificationService
- [ ] T079 [US3] Create database migration for reminders table: k8s/base/migrations/005_create_reminders.sql
- [ ] T080 [US3] Create database migration for reminder indexes: k8s/base/migrations/006_create_reminder_indexes.sql
- [ ] T081 [US3] Add logging for reminder scheduling and delivery with correlation IDs
- [ ] T082 [US3] Create MCP tool for setting reminders: src/api/mcp/tools.py#set_reminder tool with natural language parsing

**Checkpoint**: At this point, User Stories 1, 2, and 3 should all work independently

---

## Phase 6: User Story 4 - Real-time Task Synchronization (Priority: P3)

**Goal**: Implement real-time sync across clients using Kafka event streaming

**Independent Test**: Task changes propagate to connected clients within 2 seconds

### Tests for User Story 4 ⚠️

- [ ] T083 [P] [US4] Integration test for task-update event publishing in tests/integration/test_task_updates.py
- [ ] T084 [P] [US4] Test real-time sync latency in tests/e2e/test_realtime_sync.py

### Implementation for User Story 4

- [ ] T085 [P] [US4] Create TaskUpdateEvent schema: src/api/schemas/task_update.py with TaskUpdateEvent Pydantic model
- [ ] T086 [US4] Implement task-update event publishing: src/api/services/task_service.py publishes to "task-updates" topic on all CRUD operations
- [ ] T087 [US4] Create WebSocket service stub: src/api/services/websocket_service.py with broadcast_update, subscribe, unsubscribe methods
- [ ] T088 [US4] Implement task-update consumer: src/api/consumers/task_update_consumer.py consumes from "task-updates" topic
- [ ] T089 [US4] Create WebSocket endpoint: src/api/routes/websocket.py with WebSocket upgrade handling
- [ ] T090 [US4] Implement client connection management: src/api/services/connection_manager.py with add_connection, remove_connection, broadcast methods
- [ ] T091 [US4] Add correlation ID propagation from task operation to WebSocket broadcast
- [ ] T092 [US4] Add logging for WebSocket connections and message delivery

**Checkpoint**: At this point, User Stories 1-4 should all work independently

---

## Phase 7: User Story 5 - View Task Activity History (Priority: P4)

**Goal**: Implement audit trail for all task operations

**Independent Test**: User can request and view complete history of task operations

### Tests for User Story 5 ⚠️

- [ ] T093 [P] [US5] Integration test for activity history retrieval in tests/integration/test_activity_history.py
- [ ] T094 [P] [US5] Test event storage completeness in tests/integration/test_audit_trail.py

### Implementation for User Story 5

- [ ] T095 [P] [US5] Create TaskAuditEvent model: src/api/models/audit.py with fields: id, event_type, task_id, task_data (JSON), user_id, timestamp
- [ ] T096 [US5] Implement AuditService: src/api/services/audit_service.py with log_event, get_task_history, get_user_activity methods
- [ ] T097 [US5] Create task-events consumer: src/api/consumers/audit_consumer.py consumes from "task-events" topic and stores in TaskAuditEvent table
- [ ] T098 [US5] Create activity history endpoint: src/api/routes/audit.py#GET /tasks/{id}/history, GET /users/{user_id}/activity
- [ ] T099 [US5] Create MCP tool for activity history: src/api/mcp/tools.py#get_task_history tool
- [ ] T100 [US5] Create database migration for audit_events table: k8s/base/migrations/007_create_audit_events.sql
- [ ] T101 [US5] Create database migration for audit indexes: k8s/base/migrations/008_create_audit_indexes.sql (indexes on task_id, user_id, timestamp)
- [ ] T102 [US5] Implement data retention policy: src/api/services/audit_service.py#cleanup_old_events deletes events older than retention period [NEEDS CLARIFICATION: retention period]
- [ ] T103 [US5] Add pagination to activity history endpoint for large result sets

**Checkpoint**: All user stories should now be independently functional

---

## Phase 8: Dapr Integration (Cross-Cutting)

**Purpose**: Complete Dapr integration across all components

- [ ] T104 [P] Create Dapr sidecar configuration: src/dapr/configurations/dapr-sidecar.yaml with app-id, app-port, metrics-port, tracing enabled
- [ ] T105 [P] Create Kubernetes deployment with Dapr sidecar annotation: k8s/base/chat-api-deployment.yaml with dapr.io/enabled: "true", dapr.io/app-id, dapr.io/app-port
- [ ] T106 [P] Configure Dapr Pub/Sub for all event publishing: Update all event publishers to use Dapr HTTP API exclusively
- [ ] T107 [P] Configure Dapr State for conversation state: src/api/services/conversation_service.py uses Dapr State API for storing/retrieving conversation history
- [ ] T108 [P] Configure Dapr Secrets for credentials: Update database connection to retrieve credentials via Dapr Secrets API
- [ ] T109 [P] Implement Dapr Service Invocation: src/api/services/service_invocation.py for inter-service calls (if notification service is separate pod)
- [ ] T110 [P] Test Dapr Pub/Sub component: tests/integration/test_dapr_pubsub.py publishes and subscribes via Dapr
- [ ] T111 [P] Test Dapr State component: tests/integration/test_dapr_state.py saves and retrieves state via Dapr
- [ ] T112 [P] Test Dapr Jobs component: tests/integration/test_dapr_jobs.py schedules and triggers jobs
- [ ] T113 [P] Test Dapr Secrets component: tests/integration/test_dapr_secrets.py retrieves secrets via Dapr
- [ ] T114 [P] Test Dapr Service Invocation: tests/integration/test_dapr_invocation.py calls services via Dapr

---

## Phase 9: Minikube Deployment (Part B)

**Purpose**: Deploy application to local Minikube cluster with full Dapr

- [ ] T115 [P] Create Minikube namespace: k8s/overlays/minikube/namespace.yaml
- [ ] T116 [P] Create Kustomize configuration for Minikube: k8s/overlays/minikube/kustomization.yaml
- [ ] T117 [P] Create Redpanda (Kafka) deployment for Minikube: k8s/base/kafka/redpanda-deployment.yaml or use Helm chart
- [ ] T118 [P] Create Kafka topics setup script: k8s/base/kafka/create-topics.sh creates task-events, reminders, task-updates topics
- [ ] T119 [P] Update Dapr kafka-pubsub component for Minikube: k8s/overlays/minikube/kafka-pubsub-patch.yaml with local Kafka brokers
- [ ] T120 [P] Create ConfigMap for application configuration: k8s/overlays/minikube/configmap.yaml with environment-specific settings
- [ ] T121 [P] Create Kubernetes Secrets for Minikube: k8s/overlays/minikube/secrets.yaml with database connection, API keys
- [ ] T122 [P] Create service definitions: k8s/base/chat-api-service.yaml exposes FastAPI app within cluster
- [ ] T123 [P] Create ingress configuration for Minikube: k8s/overlays/minikube/ingress.yaml (optional, for external access)
- [ ] T124 [P] Write Minikube deployment script: scripts/deploy-minikube.sh automates: minikube start, dapr init -k, apply Kafka, apply Dapr components, apply app
- [ ] T125 [P] Write Minikube testing script: scripts/test-minikube.sh runs health checks and integration tests against Minikube deployment
- [ ] T126 [P] Create Minikube README: k8s/overlays/minikube/README.md with step-by-step deployment instructions
- [ ] T127 [P] Test full deployment on Minikube: Manual verification of all Dapr components, Kafka topics, and application functionality

---

## Phase 10: Cloud Deployment (Part C)

**Purpose**: Deploy application to production cloud Kubernetes (Azure AKS / Google GKE / Oracle OKE)

- [ ] T128 [P] Create cloud deployment documentation: docs/cloud-deployment.md with setup instructions for AKS, GKE, OKE
- [ ] T129 [P] Create Azure AKS overlay: k8s/overlays/cloud/aks/kustomization.yaml with AKS-specific patches
- [ ] T130 [P] Create Google GKE overlay: k8s/overlays/cloud/gke/kustomization.yaml with GKE-specific patches
- [ ] T131 [P] Create Oracle OKE overlay: k8s/overlays/cloud/oke/kustomization.yaml with OKE-specific patches
- [ ] T132 [P] Create Redpanda Cloud configuration: docs/redpanda-cloud-setup.md with step-by-step setup instructions
- [ ] T133 [P] Update Dapr kafka-pubsub for Redpanda Cloud: k8s/overlays/cloud/kafka-pubsub-cloud.yaml with SASL authentication
- [ ] T134 [P] Create cloud secrets management: k8s/overlays/cloud/secrets.yaml.template with placeholders for Redpanda credentials, database connection
- [ ] T135 [P] Create cloud deployment script: scripts/deploy-cloud.sh automates: kubectl config, dapr init -k, apply secrets, apply Dapr components, apply app
- [ ] T136 [P] Configure cloud monitoring: k8s/overlays/cloud/prometheus-servicemonitor.yaml for metrics scraping
- [ ] T137 [P] Configure cloud logging: k8s/overlays/cloud/fluentd-config.yaml for log aggregation (or cloud-native logging)
- [ ] T138 [P] Create cloud ingress configuration: k8s/overlays/cloud/ingress.yaml with TLS termination and domain configuration
- [ ] T139 [P] Write cloud deployment validation script: scripts/validate-cloud-deployment.sh checks all components are running and healthy
- [ ] T140 [P] Test deployment on chosen cloud provider (AKS/GKE/OKE): Manual verification of all functionality

---

## Phase 11: GitHub Actions CI/CD (Part C)

**Purpose**: Automate build, test, and deployment with GitHub Actions

- [ ] T141 [P] Create build and test workflow: .github/workflows/build-and-test.yaml with jobs: lint, type-check, unit-tests, integration-tests
- [ ] T142 [P] Create Minikube deployment workflow: .github/workflows/deploy-minikube.yaml triggers on PR to main, deploys to Minikube (self-hosted runner or k3d)
- [ ] T143 [P] Create cloud deployment workflow: .github/workflows/deploy-cloud.yaml triggers on tag, deploys to cloud Kubernetes
- [ ] T144 [P] Configure GitHub secrets: docs/github-actions-secrets.md documents required secrets: KUBECONFIG, REDPANDA_BROKERS, REDPANDA_USERNAME, REDPANDA_PASSWORD, DATABASE_URL, OPENAI_API_KEY
- [ ] T145 [P] Create Dockerfile for application: Dockerfile with multi-stage build, Dapr sidecar compatibility, optimized layer caching
- [ ] T146 [P] Create Docker Compose for local testing: docker-compose.yaml with app, Dapr sidecar, PostgreSQL, Redpanda (for local development without K8s)
- [ ] T147 [P] Configure container registry: .github/workflows/build-and-test.yaml includes docker build and push to GHCR
- [ ] T148 [P] Add deployment status badges: Update README.md with GitHub Actions workflow status badges
- [ ] T149 [P] Test CI/CD pipeline: Verify build, test, and deployment workflows execute successfully

---

## Phase 12: Monitoring and Logging (Part C)

**Purpose**: Configure observability for production deployment

- [ ] T150 [P] Configure application metrics: src/api/metrics.py with Prometheus metrics (request_count, request_duration, kafka_publish_count, kafka_publish_duration)
- [ ] T151 [P] Add Dapr metrics endpoint: Enable Dapr metrics on metrics-port, configure Prometheus scraping
- [ ] T152 [P] Create Grafana dashboard configuration: k8s/base/monitoring/grafana-dashboard.json with panels for requests, errors, latency, Kafka throughput
- [ ] T153 [P] Configure structured logging: Ensure all logs are JSON formatted with correlation_id, trace_id, span_id fields
- [ ] T154 [P] Create log aggregation configuration: k8s/base/monitoring/loki-config.yaml or cloud-native logging configuration
- [ ] T155 [P] Configure alerting rules: k8s/base/monitoring/alerts.yaml with alerts for high error rate, high latency, Kafka consumer lag
- [ ] T156 [P] Create health check improvements: src/api/routes/health.py#detailed_health includes Dapr connectivity, Kafka connectivity, database connectivity checks
- [ ] T157 [P] Write monitoring runbook: docs/runbooks/monitoring.md with instructions for accessing metrics, logs, and troubleshooting common issues

---

## Phase 13: Polish & Documentation

**Purpose**: Final documentation, testing, and preparation for submission

- [ ] T158 [P] Update main README.md: Include project overview, architecture diagram, quickstart for local development, deployment instructions
- [ ] T159 [P] Create Phase V specific README: specs/001-phase5-cloud/README.md with feature documentation, API reference, Dapr component documentation
- [ ] T160 [P] Create API documentation: docs/api.md with OpenAPI spec or detailed endpoint documentation
- [ ] T161 [P] Create Dapr documentation: docs/dapr-components.md explaining each Dapr component and configuration
- [ ] T162 [P] Create troubleshooting guide: docs/troubleshooting.md with common issues and solutions for Minikube, Dapr, Kafka, cloud deployment
- [ ] T163 [P] Record demo video: Create 90-second demo video showing all features, spec-driven workflow, and deployment
- [ ] T164 [P] Run full test suite: Execute all tests and ensure 90%+ code coverage
- [ ] T165 [P] Performance testing: Run load tests to verify performance goals (100 concurrent users, response times)
- [ ] T166 [P] Security review: Verify no secrets in code, proper authentication/authorization, input validation
- [ ] T167 [P] Create submission checklist: docs/submission-checklist.md with all required submission items

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order: P1 (US1, US3) → P2 (US2) → P3 (US4) → P4 (US5)
- **Dapr Integration (Phase 8)**: Can start after any user story, completes in parallel
- **Minikube Deployment (Phase 9)**: Depends on at least US1 complete
- **Cloud Deployment (Phase 10)**: Depends on Minikube deployment working
- **CI/CD (Phase 11)**: Depends on deployment scripts working
- **Monitoring (Phase 12)**: Depends on application deployed and running
- **Polish (Phase 13)**: Depends on all features complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data models but independently testable
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) - Depends on US1 task events, independently testable
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 task events, independently testable
- **User Story 5 (P4)**: Can start after Foundational (Phase 2) - Depends on task-events topic, independently testable

### Within Each User Story

- Tests marked [P] MUST be written and FAIL before implementation
- Models before services
- Services before endpoints/routes
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Setup tasks (T001-T005)**: All can run in parallel
- **Foundational tasks (T006-T018)**: All marked [P] can run in parallel
- **User Story models**: Within each story, model creation tasks marked [P] can run in parallel
- **User Story tests**: All test tasks marked [P] can run in parallel
- **Different user stories**: Can be worked on in parallel by different developers after Foundational phase
- **Dapr Integration**: Can proceed in parallel with user story implementation
- **Documentation**: Can be written in parallel with implementation

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for task creation endpoint in tests/contract/test_task_api.py"
Task: "Integration test for task CRUD operations in tests/integration/test_task_service.py"
Task: "Test Dapr Pub/Sub event publishing in tests/integration/test_event_publisher.py"

# Launch all models for User Story 1 together:
Task: "Create Task model in src/api/models/task.py"
Task: "Create Priority enum in src/api/models/priority.py"
Task: "Create TaskStatus enum in src/api/models/task_status.py"
Task: "Create RecurringPattern model in src/api/models/recurring_pattern.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 3 - Both P1)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (**CRITICAL** - blocks all stories)
3. Complete Phase 3: User Story 1 (Core task management)
4. Complete Phase 5: User Story 3 (Reminders - core differentiator)
5. **STOP and VALIDATE**: Test MVP independently
6. Deploy to Minikube and demo

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (task management) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 3 (reminders) → Test independently → Deploy/Demo
4. Add User Story 2 (search/filter/sort) → Test independently → Deploy/Demo
5. Add User Story 4 (real-time sync) → Test independently → Deploy/Demo
6. Add User Story 5 (activity history) → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Cloud Deployment Sequence

1. Minikube deployment working with all features
2. All Dapr components tested locally
3. Redpanda Cloud cluster created and tested
4. Cloud Kubernetes cluster created (AKS/GKE/OKE)
5. Deploy Dapr components to cloud
6. Deploy application to cloud
7. Configure CI/CD pipeline
8. Configure monitoring and logging

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (task management)
   - Developer B: User Story 3 (reminders + Dapr Jobs)
   - Developer C: User Story 2 (search/filter/sort)
3. After US1+US3 complete:
   - Developer A: User Story 4 (real-time sync)
   - Developer B: User Story 5 (audit trail)
   - Developer C: Minikube deployment
4. Cloud deployment and CI/CD: Team effort

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability (US1, US2, US3, US4, US5)
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD)
- Commit after each task or logical group of tasks
- Stop at checkpoints to validate story independently
- **CRITICAL**: Foundational phase (Phase 2) MUST be complete before any user story work
- **Dapr First**: All infrastructure interactions MUST go through Dapr APIs, no direct Kafka/DB client code in application layer
- **Event-Driven**: All task operations MUST publish events via Dapr Pub/Sub

---

## Task Summary by Phase

| Phase | Task Count | Key Deliverables |
|-------|------------|------------------|
| 1. Setup | 5 | Project structure, dependencies, tooling |
| 2. Foundational | 13 | Dapr client, DB connection, error handling, logging |
| 3. US1 (P1) | 25 | Task CRUD, MCP tools, events, migrations |
| 4. US2 (P2) | 16 | Search, filter, sort, indexes |
| 5. US3 (P1) | 16 | Reminders, Dapr Jobs, notification consumer |
| 6. US4 (P3) | 8 | Real-time sync, WebSocket, task-update events |
| 7. US5 (P4) | 9 | Audit trail, activity history |
| 8. Dapr Integration | 11 | Full Dapr components, testing |
| 9. Minikube | 13 | K8s manifests, deployment scripts |
| 10. Cloud Deployment | 13 | AKS/GKE/OKE overlays, Redpanda Cloud |
| 11. CI/CD | 9 | GitHub Actions workflows, Dockerfile |
| 12. Monitoring | 8 | Metrics, logging, alerting, runbooks |
| 13. Polish | 10 | Documentation, demo video, testing |
| **Total** | **166** | |

---

**Total Tasks**: 167
**Critical Path**: Setup → Foundational → US1 → US3 → Minikube → Cloud → CI/CD
**MVP Tasks**: T001-T043 (US1) + T063-T082 (US3) = ~60 tasks
**Full Implementation**: All 167 tasks
