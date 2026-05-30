# Wallet Backend — Production-Grade Upgrade Roadmap

> A phased plan to take this wallet/payments backend from a monolith prototype to a
> production-grade, distributed system — covering backend depth, infrastructure,
> distributed systems, and DevOps.

---

## Phase 1: Foundation & Code Quality

**Goal:** Eliminate technical debt, harden the codebase, and establish project hygiene.

### Concepts to Learn
- [ ] Pydantic v2 model patterns (validators, `model_config`, serialization)
- [ ] SQLModel vs raw SQLAlchemy patterns (when to use each)
- [ ] Python `typing` — generics, `TypeVar`, `Protocol`, `Literal`, `TypedDict`
- [ ] Context managers and `contextlib` patterns
- [ ] `__init__.py` patterns (lazy imports, re-exports)
- [ ] Git hooks (pre-commit, commitizen)
- [ ] EditorConfig — cross-editor consistency
- [ ] `.env` security — `.env.example`, committed secrets audit
- [ ] FastAPI `lifespan` vs `startup`/`shutdown` (deprecated)
- [ ] ASGI middleware lifecycle (send/receive wrapping)
- [ ] Exception handling patterns in FastAPI (custom `HTTPException`, `ExceptionHandler`)
- [ ] Response models vs `response_model` kwarg
- [ ] Dependency injection vs middleware — when to use each

### Features to Build
- [ ] Fix `db/session.py` — use `Config.DATABASE_URL` instead of hardcoded string
- [ ] Fix `routers/wallet.py:13` — variable shadowing bug
- [ ] Fix `routers/transaction.py:186` — query receiver by `receiver_wallet.user_id`
- [ ] Add `created_at` / `updated_at` to `User` model + migration
- [ ] Add Dramatiq broker config in `workers.py` from `Config.REDIS_URL`
- [ ] Remove committed secrets — purge `.env` from git history with `git filter-branch` or `bfg`
- [ ] Add `.env.example` with placeholder values
- [ ] Add `pre-commit` hooks (ruff, mypy, trailing-whitespace, end-of-file-fixer)
- [ ] Add `pyproject.toml` with ruff + mypy config (migrate from `requirements.txt`)
- [ ] Add comprehensive type annotations across all modules
- [ ] Add custom exception handlers for all API routes
- [ ] Extract reusable dependency callables into `dependencies/`
- [ ] Centralize HTTP status codes (use `status` module, not magic numbers)
- [ ] Add response models to all endpoints for OpenAPI docs quality

---

## Phase 2: Testing Infrastructure

**Goal:** Build a comprehensive test suite at every level of the test pyramid.

### Concepts to Learn
- [ ] `pytest` fixtures, `conftest.py`, `tmp_path`, `monkeypatch`
- [ ] `httpx.AsyncClient` with ASGI `transport`
- [ ] Mocking vs dependency override in FastAPI (`app.dependency_overrides`)
- [ ] Test database strategies — in-memory SQLite vs test containers
- [ ] Factory pattern for test data (e.g., `factory_boy`)
- [ ] Faker for realistic test data generation
- [ ] Parametrized tests (`@pytest.mark.parametrize`)
- [ ] Coverage reporting (`pytest-cov`)
- [ ] Property-based testing (`hypothesis`)
- [ ] Testing idempotency middleware (Redis mock/override)
- [ ] Testing WebSocket endpoints (`httpx` + `websockets`)
- [ ] Testing Dramatiq workers (in-process broker)
- [ ] Snapshot testing (`syrupy`)
- [ ] Load testing with `locust` or `k6`
- [ ] Mutation testing (`mutmut`) — measuring test quality

### Features to Build
- [ ] Set up `tests/` directory with `conftest.py` — async test client, test DB session, Redis mock
- [ ] Unit test: `core/security.py` — password hashing, JWT creation/verification
- [ ] Unit test: `db/models.py` — model constraints, relationships, defaults
- [ ] Integration test: `POST /signup` — creation, duplicate email, validation errors
- [ ] Integration test: `POST /token` — valid login, wrong password, missing fields
- [ ] Integration test: `GET /users/me` — with/without token, invalid token
- [ ] Integration test: `POST /wallet` — create, duplicate (one-per-user), missing auth
- [ ] Integration test: `GET /wallet` — own wallet, no wallet
- [ ] Integration test: `DELETE /wallet` — delete, no wallet, with balance
- [ ] Integration test: `PATCH /transaction/deposit` — success, invalid amount, currency mismatch
- [ ] Integration test: `PATCH /transaction/withdraw` — success, insufficient balance
- [ ] Integration test: `PATCH /transaction/transfer` — success, self-transfer, wallet not found
- [ ] Integration test: double-entry ledger — every transaction creates exactly 2 `LedgerEntry` rows
- [ ] Integration test: idempotency — replaying same `X-Idempotency-Key` returns cached response
- [ ] Integration test: rate limiting — exceeding limit returns 429
- [ ] Integration test: WebSocket — connect, perform transaction, receive event
- [ ] Integration test: `GET /transaction/history` — pagination, ordering
- [ ] Integration test: `GET /transaction/{id}/ledger` — entries exist, correct
- [ ] Property-based test: wallet balance invariants
- [ ] Property-based test: transaction integrity (sum of debits == sum of credits)
- [ ] Mock test: Dramatiq email worker receives correct payload
- [ ] Load test: concurrent transfers on same wallet (race conditions)
- [ ] Smoke test: `uvicorn main:app` boots, all endpoints respond, Alembic generates cleanly
- [ ] Achieve >90% code coverage; add CI gate at 80%

---

## Phase 3: PostgreSQL & Database Operations

**Goal:** Migrate from SQLite to PostgreSQL and master production database patterns.

### Concepts to Learn
- [ ] PostgreSQL vs SQLite — feature gaps (enums, partial indexes, `RETURNING`, CTEs)
- [ ] `asyncpg` vs `aiosqlite` — connection pooling, prepared statements
- [ ] PostgreSQL connection pooling — `pgbouncer` modes (transaction vs session)
- [ ] Alembic — async migrations, autogenerate quirks with PostgreSQL
- [ ] Database indexes — B-tree, hash, GIN, GiST, partial, covering indexes
- [ ] SQL `EXPLAIN ANALYZE` — reading query plans
- [ ] Connection pool tuning — `min_size`, `max_size`, overflow, timeout
- [ ] Migration strategies — zero-downtime migrations (expand/migrate/contract)
- [ ] Lock types in PostgreSQL — `ROW EXCLUSIVE`, `ACCESS EXCLUSIVE`, deadlocks
- [ ] Isolation levels — `READ COMMITTED` vs `REPEATABLE READ` vs `SERIALIZABLE`
- [ ] Advisory locks in PostgreSQL
- [ ] `SKIP LOCKED` and `NOWAIT` for queue-like tables
- [ ] Read replicas — setting up, routing reads vs writes
- [ ] Database backup strategies — `pg_dump`, WAL archiving, PITR
- [ ] `pg_stat_statements` — query performance monitoring

### Features to Build
- [ ] Add `asyncpg` + `SQLAlchemy asyncpg` driver to dependencies
- [ ] Create `docker-compose.yml` with PostgreSQL + Redis for local dev
- [ ] Update `Config.DATABASE_URL` handling for PostgreSQL
- [ ] Create Alembic migration switching SQLite → PostgreSQL schema
- [ ] Add proper enums for `TransactionType` and `EntryType` (PostgreSQL ENUM)
- [ ] Add indexes on `transaction(from_wallet_id, created_at)`, `transaction(to_wallet_id, created_at)`, `ledger_entry(wallet_id, created_at)`
- [ ] Add partial index on `transaction(created_at)` for history queries
- [ ] Add database migration for adding read replica support
- [ ] Implement read/write session routing (separate engine for reads)
- [ ] Add `pg_stat_statements` extension and query performance tracking
- [ ] Create backup script (`pg_dump` + S3 upload)
- [ ] Add database migration zero-downtime strategy guide
- [ ] Benchmark query performance with `EXPLAIN ANALYZE`

---

## Phase 4: Observability

**Goal:** Full visibility into system health — logs, metrics, traces, and alerting.

### Concepts to Learn
- [ ] Structured logging — `structlog` vs `python-json-logger`, context variables
- [ ] Log levels — when to use DEBUG, INFO, WARNING, ERROR, CRITICAL
- [ ] Correlation IDs — threading through async context (`contextvars`)
- [ ] OpenTelemetry — traces, spans, `tracer.start_as_current_span`
- [ ] Distributed tracing — trace propagation (W3C TraceContext, B3)
- [ ] Prometheus metric types — Counter, Gauge, Histogram, Summary
- [ ] RED metrics (Rate, Errors, Duration) for services
- [ ] USE metrics (Utilization, Saturation, Errors) for resources
- [ ] Four golden signals — Latency, Traffic, Errors, Saturation
- [ ] Grafana dashboard design — panel types, transformations, annotations
- [ ] Alerting — PromQL for alert rules, Alertmanager routing
- [ ] Sentry — error grouping, releases, performance monitoring
- [ ] Health check patterns — readiness vs liveness probes
- [ ] Application Performance Monitoring (APM) concepts

### Features to Build
- [ ] Add `core/logging_config.py` with `structlog` JSON rendering
- [ ] Replace all `print()` calls with structured logging
- [ ] Add request correlation ID middleware (propagate via `contextvars`)
- [ ] Add OpenTelemetry instrumentation — auto-instrument FastAPI, SQLAlchemy, Redis, httpx
- [ ] Add OpenTelemetry exporter to Jaeger or Grafana Tempo
- [ ] Add `prometheus-fastapi-instrumentator` in `main.py`
- [ ] Add custom Prometheus metrics — `wallet_transactions_total` (by type), `wallet_balance` gauge, `ledger_entries_total`
- [ ] Add Prometheus metrics for Dramatiq queue depth
- [ ] Add Prometheus metrics for database connection pool size, active connections
- [ ] Expose `/metrics` endpoint
- [ ] Add Sentry initialization with release tracking
- [ ] Add health check endpoints — `GET /health/ready`, `GET /health/live` (DB + Redis checks)
- [ ] Create `docker-compose.yml` with Prometheus + Grafana + Jaeger
- [ ] Create Grafana dashboard — API request rate/errors/latency, DB queries, queue depth
- [ ] Create alert rules — high error rate, high latency, queue backlog
- [ ] Write alerting runbook for each rule

---

## Phase 5: Containerization & CI/CD

**Goal:** Reliable, reproducible builds and automated delivery pipeline.

### Concepts to Learn
- [ ] Docker multi-stage builds — builder pattern, distroless images
- [ ] Docker layer caching — dependency ordering
- [ ] Docker Compose — healthchecks, depends_on, network isolation
- [ ] Dockerfile best practices — non-root user, `--no-cache-dir`, `.dockerignore`
- [ ] GitHub Actions — workflow syntax, matrix builds, caching, artifacts
- [ ] CI pipeline stages — lint → type-check → test → build → security-scan
- [ ] CD pipeline — staging deploy → integration tests → production deploy
- [ ] Semantic versioning — `__version__`, git tags, changelog
- [ ] Container image tagging — git SHA, semantic version, latest
- [ ] Docker image registries — Docker Hub, GitHub Container Registry, ECR
- [ ] `docker scout` or `trivy` for container vulnerability scanning
- [ ] Secrets in CI — GitHub Actions secrets, not in code

### Features to Build
- [ ] Create `.dockerignore`
- [ ] Create multi-stage `Dockerfile` — builder stage with dev deps, runtime stage with distroless image
- [ ] Create `Dockerfile.worker` for Dramatiq worker
- [ ] Create `docker-compose.yml` with app, worker, PostgreSQL, Redis, Prometheus, Grafana
- [ ] Create `.github/workflows/ci.yml` — lint (ruff), type-check (mypy), test (pytest + coverage), build image
- [ ] Create `.github/workflows/cd.yml` — build & push image, deploy to staging, run smoke tests, promote to production
- [ ] Add `docker-compose.prod.yml` overlay (resource limits, restart policies, logging driver)
- [ ] Add healthcheck to Dockerfiles (`curl --fail http://localhost:8000/health/live`)
- [ ] Add docker compose healthchecks for PostgreSQL (pg_isready) and Redis (redis-cli ping)
- [ ] Configure GitHub Actions cache for pip and Docker layers
- [ ] Add `trivy` or `snyk` security scanning to CI

---

## Phase 6: Rate Limiting, Security & API Hardening

**Goal:** Production-grade security posture and API protection.

### Concepts to Learn
- [ ] Rate limiting algorithms — token bucket, leaky bucket, sliding window, fixed window
- [ ] Rate limiting at different layers — application vs API gateway vs load balancer
- [ ] JWT best practices — short expiry, refresh tokens, rotation, revocation
- [ ] Password policies — entropy, breach detection (HaveIBeenPwned API), salt rotation
- [ ] OAuth2 flows — authorization code, client credentials, PKCE
- [ ] CORS — preflight, allowed origins, credentials policy
- [ ] Security headers — `Strict-Transport-Security`, `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`
- [ ] Input validation — injection prevention, sanitization, `allowlist` vs `denylist`
- [ ] SQL injection prevention with ORM parameterized queries
- [ ] API key management — hashing, prefix identification, rotation
- [ ] Secrets management — HashiCorp Vault, AWS Secrets Manager, `sops`
- [ ] HTTPS/SSL — `certbot`, Let's Encrypt, `nginx` reverse proxy
- [ ] Web Application Firewall (WAF) — modsecurity, Cloudflare, AWS WAF
- [ ] PCI-DSS considerations for payment systems — data encryption, access control, audit trails
- [ ] DDoS protection strategies — rate limiting, CDN, connection limiting
- [ ] `bcrypt` work factor tuning — cost vs security

### Features to Build
- [ ] Add `fastapi-limiter` with Redis backend in `core/limiter.py`
- [ ] Configure rate limits — `POST /signup`: 5/min, `POST /token`: 5/min, `PATCH /withdraw|transfer`: 10/min, `PATCH /deposit`: 30/min
- [ ] Add refresh token flow — `/token/refresh` endpoint with longer-lived refresh token
- [ ] Add JWT blacklisting on logout (Redis set with TTL matching token expiry)
- [ ] Add password breach check on signup (k-anonymity API)
- [ ] Add CORS middleware with strict allowed origins from config
- [ ] Add security headers middleware (use `SecureHeaders` or Starlette middleware)
- [ ] Add API key authentication option for programmatic access
- [ ] Add request body size limiting middleware
- [ ] Add SQL injection fuzzing test
- [ ] Add secret scanning to CI (`trufflehog`, `gitleaks`)
- [ ] Add HTTPS termination config for production deployment (nginx/Caddy)

---

## Phase 7: Advanced API Patterns & Real-Time

**Goal:** Production API versioning, WebSocket streaming, comprehensive documentation.

### Concepts to Learn
- [ ] API versioning — URL prefix vs header vs content negotiation
- [ ] OpenAPI / Swagger — schema customization, examples, groups, tags
- [ ] WebSocket protocol — frames, ping/pong, close codes, backpressure
- [ ] WebSocket authentication — token in query param vs first message
- [ ] Redis Pub/Sub — channels, pattern matching, `PUBLISH`/`SUBSCRIBE`
- [ ] Server-Sent Events (SSE) — vs WebSocket for one-directional streaming
- [ ] GraphQL — when it makes sense over REST for wallet queries
- [ ] Pagination patterns — cursor-based vs offset-based, keyset pagination
- [ ] Bulk operations — batch endpoints, `TransferBatchRequest`
- [ ] Async task status — `/tasks/{id}/status` with Webhook or polling
- [ ] Request validation — Pydantic `Field(..., examples=...)`, custom validators
- [ ] Rate limit headers — `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- [ ] `Retry-After` header for 429 responses

### Features to Build
- [ ] Add API version prefix (`/v1/...`) to all routes
- [ ] Maintain backward-compatible `/` routes with deprecation header
- [ ] Implement WebSocket endpoint — `WS /v1/ws` — auth via token, subscribe to wallet updates
- [ ] Add Redis Pub/Sub channel `wallet:events` — publish after deposit/withdraw/transfer
- [ ] Add Redis Pub/Sub listener in FastAPI lifespan for broadcasting
- [ ] Add SSE endpoint for transaction history streaming
- [ ] Add cursor-based pagination to `GET /v1/transaction/history`
- [ ] Add `GET /v1/transactions/{id}` for single transaction detail
- [ ] Add batch transfer endpoint — `POST /v1/transfers/batch`
- [ ] Add async task status endpoint with webhook notification
- [ ] Add comprehensive OpenAPI examples on all endpoints
- [ ] Add rate limit response headers to all endpoints
- [ ] Add proper 429 response body with `Retry-After` and rate limit info

---

## Phase 8: Event-Driven Architecture & Message Queues

**Goal:** Decouple services, enable async processing, and build resilient event pipelines.

### Concepts to Learn
- [ ] Message queue patterns — point-to-point vs pub/sub
- [ ] Kafka — topics, partitions, consumer groups, offsets, retention
- [ ] RabbitMQ — exchanges (direct, topic, fanout, headers), queues, bindings
- [ ] Kafka vs RabbitMQ — when to use which
- [ ] Exactly-once vs at-least-once vs at-most-once delivery semantics
- [ ] Consumer offset management — auto-commit vs manual commit
- [ ] Dead letter queues (DLQ) — handling poison messages
- [ ] Retry strategies — exponential backoff, max retries, retry queues
- [ ] Idempotent consumers — deduplication, upsert patterns
- [ ] Event schema management — Avro, Protobuf, Schema Registry
- [ ] Event versioning — backward/forward compatibility
- [ ] Circuit breaker pattern — state machine (closed/open/half-open)
- [ ] Bulkhead pattern — isolating thread pools/queues per consumer
- [ ] Backpressure handling — consumer lag monitoring, rate limiting

### Features to Build
- [ ] Add Kafka/RabbitMQ producer — publish `TransactionCreated`, `LedgerEntryCreated`, `WalletBalanceChanged`
- [ ] Add Kafka/RabbitMQ consumer for email notifications (replace Dramatiq)
- [ ] Add Kafka/RabbitMQ consumer for audit logging
- [ ] Add dead letter queue for failed events
- [ ] Add retry queue with exponential backoff
- [ ] Add consumer health monitoring — lag, error rate
- [ ] Add event schema registry with Avro/Protobuf
- [ ] Add circuit breaker for external dependencies (email, queue)
- [ ] Add bulkhead isolation per event type
- [ ] Add consumer idempotency — deduplicate by event ID
- [ ] Monitor and alert on consumer lag

---

## Phase 9: Distributed Systems Patterns

**Goal:** Build reliability and consistency patterns for a distributed wallet system.

### Concepts to Learn
- [ ] Saga pattern — choreography vs orchestration, compensating transactions
- [ ] Outbox pattern — transactional outbox table, CDC (change data capture)
- [ ] Two-Phase Commit (2PC) — coordinator, prepare/commit/rollback
- [ ] SAGA vs 2PC — when to use which
- [ ] Event sourcing — event store, projection, rebuild state from events
- [ ] CQRS (Command Query Responsibility Segregation) — separate read/write models
- [ ] CAP theorem — consistency, availability, partition tolerance tradeoffs
- [ ] PACELC theorem — partition-tolerant systems tradeoff latency vs consistency
- [ ] Distributed consensus — Raft, Paxos (conceptual understanding)
- [ ] Distributed ID generation — Snowflake, ULID, UUIDv7
- [ ] Clock skew issues — vector clocks, hybrid logical clocks (HLC)
- [ ] CRDTs (Conflict-Free Replicated Data Types) — for balance reconciliation
- [ ] Write-ahead log (WAL) — PostgreSQL WAL, logical replication, `pgoutput`
- [ ] Change Data Capture — Debezium, Kafka Connect
- [ ] Leader election — for scheduled task singletons

### Features to Build
- [ ] Implement transactional outbox — write events to `outbox` table in same DB transaction as wallet update
- [ ] Add outbox relay — background worker that reads `outbox` and publishes to message queue
- [ ] Implement Saga for cross-service transactions (e.g., transfer between shards)
- [ ] Add compensating transaction rollback for failed Saga steps
- [ ] Implement event-sourced wallet balance — rebuild balance from ledger event stream
- [ ] Add CQRS layer — separate read model for transaction history (denormalized)
- [ ] Add distributed ID generator (Snowflake-style) for transactions
- [ ] Add CDC pipeline — Debezium streaming `outbox` table → Kafka
- [ ] Add balance reconciliation job — diff computed vs stored balance, alert on mismatch
- [ ] Implement distributed lock for wallet operations (Redis Redlock)

---

## Phase 10: Scalability & Performance

**Goal:** Handle increasing load through horizontal scaling and optimization.

### Concepts to Learn
- [ ] Horizontal vs vertical scaling — when each makes sense
- [ ] Database sharding — hash-based vs range-based, shard key selection
- [ ] Read replicas — read/write splitting, replication lag handling
- [ ] Caching strategies — cache-aside, write-through, write-behind, cache invalidation
- [ ] Redis cache patterns — rate limiting, session store, API response cache
- [ ] Connection pooling — database, HTTP, Redis pool sizing
- [ ] Async optimization — `asyncio` event loop, `await` patterns, `gather`
- [ ] N+1 query problem — eager loading, `selectinload`, `joinedload`
- [ ] Lazy loading vs eager loading in SQLAlchemy
- [ ] Database query optimization — index-only scans, covering indexes
- [ ] Python profiling — `cProfile`, `py-spy`, `scalene`
- [ ] Memory profiling — `memory_profiler`, `tracemalloc`
- [ ] GIL considerations for CPU-bound tasks
- [ ] Load balancing — round-robin, least connections, IP hash, consistent hashing
- [ ] Auto-scaling — CPU-based, request-based, scheduled
- [ ] CDN for static assets — admin dashboard assets
- [ ] Compression — gzip/brotli for API responses

### Features to Build
- [ ] Add Redis caching layer for wallet balance reads (`GET /wallet`)
- [ ] Add Redis caching for transaction history (TTL-based invalidation)
- [ ] Add cache invalidation on write — publish `wallet:balance:changed` event
- [ ] Optimize transaction history query — add composite indexes, keyset pagination
- [ ] Fix N+1 queries in transaction history (eager load sender/receiver names)
- [ ] Add database connection pool tuning — configurable pool size, overflow
- [ ] Add HTTP keep-alive and connection pooling for httpx/Brevo calls
- [ ] Profile application with `py-spy` — identify hot paths
- [ ] Profile database queries — identify slow queries, missing indexes
- [ ] Add database read replicas — route `GET /history` to read replica
- [ ] Add auto-scaling config for container orchestrator
- [ ] Add response compression middleware (gzip/brotli)
- [ ] Benchmark with k6 — 100, 500, 1000 concurrent users
- [ ] Tune `asyncio` — `uvicorn` workers, `--workers` flag with `gunicorn`
- [ ] Add database sharding simulation — partition wallets by `wallet_id % N`

---

## Phase 11: Infrastructure as Code & Cloud Deployment

**Goal:** Manage infrastructure declaratively, deploy to the cloud.

### Concepts to Learn
- [ ] Infrastructure as Code (IaC) — declarative vs imperative, state management
- [ ] Terraform — `main.tf`, modules, remote state, `terraform plan/apply`
- [ ] Pulumi — infrastructure as real code (Python/TypeScript)
- [ ] Kubernetes — pods, deployments, services, configmaps, secrets, ingress
- [ ] Helm — chart structure, templates, values, dependencies
- [ ] Kubernetes Operators — custom resource definitions (CRDs)
- [ ] Service mesh — Istio/Linkerd (mTLS, traffic splitting, observability)
- [ ] Cloud provider basics — AWS / GCP / Azure core services
- [ ] Managed PostgreSQL — AWS RDS, GCP Cloud SQL, connection via IAM
- [ ] Managed Redis — AWS ElastiCache, GCP Memorystore
- [ ] Managed Kafka — AWS MSK, Confluent Cloud, Redpanda
- [ ] Object storage — AWS S3, GCP Cloud Storage (backups, logs)
- [ ] IAM — roles, policies, least-privilege principle
- [ ] VPC — private/public subnets, NAT gateway, security groups
- [ ] DNS — Route53, Cloudflare, `external-dns`
- [ ] TLS certificate management — `cert-manager` on Kubernetes
- [ ] Cost management — resource tagging, reserved instances, right-sizing

### Features to Build
- [ ] Create Terraform module for VPC + subnets + security groups
- [ ] Create Terraform module for RDS PostgreSQL (multi-AZ, automated backups)
- [ ] Create Terraform module for ElastiCache Redis (cluster mode)
- [ ] Create Terraform module for ECS Fargate or EKS cluster
- [ ] Create Terraform module for S3 bucket (Terraform state, backups, logs)
- [ ] Create Terraform module for IAM roles and policies
- [ ] Create Helm chart for wallet app — deployment, HPA, service, ingress
- [ ] Create Helm chart for Dramatiq worker
- [ ] Add Kubernetes manifests — `Deployment`, `Service`, `Ingress`, `ConfigMap`, `Secret` (external)
- [ ] Add `HorizontalPodAutoscaler` — CPU/memory-based
- [ ] Add `PodDisruptionBudget` — ensure min availability
- [ ] Add service mesh sidecar injection (Istio/Linkerd)
- [ ] Configure `cert-manager` for automatic TLS
- [ ] Add Terraform state locking with DynamoDB
- [ ] Add `external-dns` for automatic DNS records
- [ ] Create Makefile — `make dev`, `make test`, `make build`, `make deploy`

---

## Phase 12: GitOps & Advanced DevOps

**Goal:** Fully automated, auditable deployments and operational maturity.

### Concepts to Learn
- [ ] GitOps — ArgoCD / Flux, desired state in git, auto-sync
- [ ] ArgoCD — application, project, sync policy, sync waves
- [ ] Blue-green deployment — traffic switching, rollback
- [ ] Canary deployment — progressive traffic shifting, metrics-based promotion
- [ ] Feature flags — LaunchDarkly, Unleash, Flagsmith
- [ ] A/B testing — experiment design, statistical significance
- [ ] Chaos engineering — principles, Chaos Mesh, LitmusChaos
- [ ] GameDay exercises — planned failure scenarios, postmortems
- [ ] Blameless postmortems — incident timeline, root cause, action items
- [ ] SLA / SLO / SLI — service level indicators, objectives, agreements
- [ ] Error budgets — velocity vs reliability tradeoff
- [ ] Runbooks — incident response procedures for common failures
- [ ] On-call — escalation policies, pager duty rotation, alert fatigue

### Features to Build
- [ ] Install and configure ArgoCD — sync wallet app from git repo
- [ ] Create ArgoCD Application manifests for each component
- [ ] Implement blue-green deployment — separate service + ingress, traffic switching
- [ ] Add canary deployment config — Flagger or Argo Rollouts
- [ ] Add feature flag system — `POST /v1/admin/flags`, per-route middleware
- [ ] Write SLA/SLO document — target 99.9% uptime, p95 latency <200ms
- [ ] Create SLI dashboards in Grafana — availability, latency, error rate
- [ ] Set error budget burn rate alerts
- [ ] Write incident response runbooks — DB failure, queue backlog, high latency
- [ ] Set up on-call schedule with escalation
- [ ] Add Chaos Mesh experiments — pod kill, network latency, DB connection failure
- [ ] Run GameDay exercises — simulate DB failover, queue outage
- [ ] Build runbook automation — Slack/PagerDuty webhooks with context

---

## Phase 13: Advanced Security & Compliance

**Goal:** Meet financial system security standards and compliance requirements.

### Concepts to Learn
- [ ] PCI-DSS — 12 requirements for cardholder data (relevant concepts)
- [ ] PII handling — data classification, encryption at rest, access logging
- [ ] Encryption at rest — PostgreSQL TDE, application-level encryption
- [ ] Encryption in transit — mTLS between services, TLS 1.3
- [ ] Secrets management — HashiCorp Vault, AWS Secrets Manager, `external-secrets` operator
- [ ] Audit logging — immutable audit trails, who accessed what and when
- [ ] Data retention policies — GDPR right to deletion, financial record retention
- [ ] Penetration testing — OWASP Top 10, automated scanners, manual testing
- [ ] Vulnerability management — CVE scanning, patch cadence
- [ ] Dependency security — Dependabot, Renovate, `pip-audit`
- [ ] Supply chain security — `SLSA` framework, signed artifacts
- [ ] Fraud detection — rule-based, ML models, velocity checks
- [ ] KYC/AML concepts — identity verification, transaction monitoring
- [ ] Rate limiting abuse — distributed brute force, credential stuffing
- [ ] Session management — device fingerprint, concurrent session limits

### Features to Build
- [ ] Add audit logging — `AuditLog` table with user_id, action, resource, timestamp, IP address
- [ ] Add audit log middleware — log all mutating requests
- [ ] Add PII encryption — encrypt email and name at rest (AES-256-GCM)
- [ ] Integrate with external secrets — Vault or AWS Secrets Manager via `external-secrets`
- [ ] Add `pip-audit` to CI pipeline
- [ ] Add Dependabot / Renovate config for automated dependency updates
- [ ] Add fraud detection rules engine — velocity check (same IP, multiple wallets), amount thresholds
- [ ] Add KYC verification placeholder endpoint
- [ ] Add rate limiting on IP in addition to user token
- [ ] Add device fingerprinting for session tracking
- [ ] Add session limit — max N concurrent sessions per user
- [ ] Add penetration testing checklist (OWASP-based) in `docs/security.md`
- [ ] Add data retention job — archive/delete records per policy
- [ ] Run `trufflehog` on git history to detect any committed secrets

---

## Phase 14: Microservices Decomposition

**Goal:** Split the monolith into independently deployable services.

### Concepts to Learn
- [ ] Service boundaries — bounded contexts, domain-driven design (DDD)
- [ ] Strangler fig pattern — incremental migration from monolith
- [ ] Inter-service communication — gRPC vs HTTP REST vs async messaging
- [ ] gRPC — protobuf definitions, streaming, bidirectional
- [ ] Service discovery — Consul, Kubernetes DNS, Eureka
- [ ] API Gateway — Kong, Tyk, Envoy, AWS API Gateway
- [ ] Rate limiting and auth at gateway level
- [ ] Service mesh — Istio mTLS, traffic policies, observability
- [ ] Distributed tracing across services — W3C TraceContext propagation
- [ ] Shared data vs database-per-service
- [ ] Event collaboration — services communicate via events only
- [ ] Transactional sagas across services — orchestration vs choreography
- [ ] Contract testing — Pact, `pytest-pact`
- [ ] Schema registry for cross-service event contracts

### Features to Build
- [ ] Identify bounded contexts — Auth, Wallet, Ledger, Notification, Admin
- [ ] Create `services/auth-service/` — user management, JWT issuance
- [ ] Create `services/wallet-service/` — balance management, wallet CRUD
- [ ] Create `services/ledger-service/` — double-entry entries, audit trail
- [ ] Create `services/notification-service/` — email, WebSocket, webhook
- [ ] Create `services/gateway/` — API gateway (Kong/Tyk or custom Envoy config)
- [ ] Create `services/analytics-service/` — transaction reporting, fraud detection
- [ ] Migrate Auth endpoints → Auth Service (strangler fig)
- [ ] Migrate Wallet endpoints → Wallet Service
- [ ] Migrate Transaction endpoints → Wallet Service + Ledger Service
- [ ] Add gRPC contracts between services (protobuf definitions)
- [ ] Add service discovery — Kubernetes DNS or Consul
- [ ] Add contract tests between services (Pact)
- [ ] Add cross-service Saga — transfer funds involving Wallet + Ledger
- [ ] Add API gateway routing — rate limiting, auth, versioning at edge
- [ ] Add cross-service tracing with OpenTelemetry propagation

---

## Phase 15: Production Operations & Reliability Engineering

**Goal:** Achieve operational excellence with mature Site Reliability Engineering practices.

### Concepts to Learn
- [ ] SRE principles — error budgets, toil reduction, SLIs/SLOs/SLAs
- [ ] Capacity planning — peak load estimation, resource sizing, growth forecasting
- [ ] Disaster recovery — RPO (Recovery Point Objective), RTO (Recovery Time Objective)
- [ ] Multi-region deployment — active-active vs active-passive
- [ ] Database failover — automated failover, read replica promotion
- [ ] Data replication — synchronous vs asynchronous, CDC for cross-region
- [ ] Backup validation — automated restore testing
- [ ] Chaos engineering in production — blast radius, experiment design
- [ ] Load shedding — graceful degradation, prioritized requests
- [ ] Throttling — per-user, per-tier, per-endpoint
- [ ] Cost optimization — reserved instances, spot instances, right-sizing
- [ ] Vendor lock-in mitigation — abstractions for portable infrastructure
- [ ] Post-incident reviews — structured analysis, action tracking

### Features to Build
- [ ] Define SLOs — API availability (99.9%), p95 latency (<200ms), error rate (<0.1%)
- [ ] Create SLO burn-rate alerts — 1h, 6h, 72h windows
- [ ] Set up multi-region deployment — primary in us-east-1, DR in us-west-2
- [ ] Set up cross-region database replication
- [ ] Write DR runbook — failover steps, RTO/RPO targets, testing schedule
- [ ] Add automated DR testing — quarterly failover drill
- [ ] Add backup validation — weekly restore test to staging
- [ ] Add request prioritization — premium users get higher rate limits
- [ ] Add load shedding — `GET /health` always responds, non-critical endpoints can be degraded
- [ ] Add infrastructure cost tracking — per-service, per-environment
- [ ] Set up scheduled cost optimization review
- [ ] Create post-incident review template
- [ ] Track reliability improvements in monthly SLO reviews
- [ ] Build a dashboard — current vs target SLOs, error budget remaining
