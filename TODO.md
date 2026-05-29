# Wallet Backend — Upgrade Roadmap

## Phase 1: Foundation Fixes

- [ ] Use `Config.DATABASE_URL` in `db/session.py` instead of hardcoded string
- [ ] Fix `routers/wallet.py` variable shadowing bug (line 13 overwrites `wallet` param)
- [ ] Fix `routers/transaction.py:186` — query receiver by `receiver_wallet.user_id` (not `.id`)
- [ ] Add `created_at` / `updated_at` to `User` model
- [ ] Add Dramatiq broker config in `workers.py` so it works out of the box

---

## Phase 2: Double-Entry Ledger

### Model (`db/models.py`)
- [ ] Add `LedgerEntry` table:
  - `id`, `transaction_id` (FK → transaction), `wallet_id` (FK → wallet)
  - `entry_type` (DEBIT / CREDIT), `amount`, `currency`
  - `balance_snapshot` (wallet balance after this entry)
  - `created_at` (immutable, server default)
  - Unique constraint on `(transaction_id, entry_type)`

### Transaction endpoints (`routers/transaction.py`)
- [ ] `withdraw`: create DEBIT entry for sender + CREDIT entry to system (or null)
- [ ] `deposit`: create DEBIT entry from system (or null) + CREDIT entry for receiver
- [ ] `transfer`: create DEBIT entry for sender + CREDIT entry for receiver
- [ ] Wrap wallet balance update + ledger entries in a single DB transaction
- [ ] Move email sending to after commit (already done, but wrap in try/except)

### History endpoint
- [ ] Optionally expose ledger entries via `/transaction/{id}/ledger`

---

## Phase 3: Centralized Redis

### `core/redis.py` (new)
- [ ] Single `async` Redis client instance (from `Config.REDIS_URL`)
- [ ] Helper functions: `get_redis()`, `close_redis()`
- [ ] Lifecycle managed via FastAPI `lifespan`

### Update consumers
- [ ] `middleware/idempotency.py` → import shared redis from `core/redis.py`
- [ ] `workers.py` → configure Dramatiq Redis broker

---

## Phase 4: Rate Limiting

### Install `fastapi-limiter`
- [ ] Init in `main.py` lifespan (connects to Redis)
- [ ] Apply `@limiter.limit("5/minute")` to:
  - `POST /signup`
  - `POST /token`
- [ ] Apply `@limiter.limit("10/minute")` to:
  - `PATCH /transaction/withdraw`
  - `PATCH /transaction/transfer`
- [ ] Apply `@limiter.limit("30/minute")` to:
  - `PATCH /transaction/deposit`
- [ ] No limit on:
  - `GET /transaction/history`
  - `GET /wallet`
  - `GET /users/me`

---

## Phase 5: Real-Time WebSockets

### `routers/ws.py` (new)
- [ ] `WS /ws` — authenticate via token query param, subscribe to wallet updates
- [ ] Use Redis Pub/Sub channel `wallet:events` to broadcast across instances
- [ ] Publish events after every deposit / withdraw / transfer

### `main.py`
- [ ] Add WebSocket router
- [ ] Add Redis Pub/Sub listener task in lifespan

---

## Phase 6: Admin HTMX Dashboard

### Directory structure
```
templates/
├── base.html          # Layout with Tailwind CSS CDN
├── dashboard.html     # Main dashboard page
└── partials/
    ├── transactions.html   # Transaction list (HTMX partial)
    ├── users.html          # Active users
    ├── wallet_health.html  # Balance / wallet stats
    └── queue_depth.html    # Queue / job stats
```

### `routers/admin.py` (new)
- [ ] `GET /admin` — render dashboard
- [ ] `GET /admin/transactions` — HTMX partial for transaction list
- [ ] `GET /admin/users` — HTMX partial for active users
- [ ] `GET /admin/wallet-health` — HTMX partial for wallet stats
- [ ] `GET /admin/queue-depth` — HTMX partial for Dramatiq queue depth (stub)

### Auth
- [ ] Admin endpoints protected by a simple middleware or token check

---

## Phase 7: Observability

### Structured logging
- [ ] Add `core/logging_config.py`
- [ ] Configure `structlog` with JSON rendering
- [ ] Replace `print()` calls in `workers.py` with proper logging

### Prometheus metrics
- [ ] `prometheus-fastapi-instrumentator` in `main.py`
- [ ] Custom metrics: `wallet_transactions_total`, `wallet_balance` gauge, `ledger_entries_total`
- [ ] Expose `/metrics` endpoint

---

## Phase 8: Testing & Verification

### Tests
- [ ] `pytest` + `httpx` AsyncClient
- [ ] Test ledger double-entry: every transaction creates 2 entries
- [ ] Test idempotency: replaying same key returns cached response
- [ ] Test rate limiting: exceeding limit returns 429
- [ ] Test WebSocket: connect, perform transaction, receive event

### Smoke test
- [ ] `uvicorn main:app` boots without errors
- [ ] All endpoints respond correctly
- [ ] Alembic migrations generate cleanly

---

## Future Phases (after monolith is solid)

- [ ] Kafka / RabbitMQ event bus
- [ ] Saga / Outbox pattern for distributed transactions
- [ ] Sharding wallets by user ID
- [ ] Fraud detection rules engine
- [ ] Multi-currency support (exchange rates, conversion)
- [ ] Event sourcing (full replay from ledger entries)
- [ ] Microservice split (auth, wallet, ledger, notification)
- [ ] Grafana dashboards + distributed tracing (OpenTelemetry)
