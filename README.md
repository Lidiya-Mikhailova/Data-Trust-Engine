# Data Trust Engine

Production-oriented data engineering platform for building reliable ETL pipelines with automatic source failover, trust-based decision making, and built-in observability. The platform ingests data from multiple independent sources, evaluates their reliability in real time, transforms data through a Medallion Architecture (Bronze / Silver / Gold), and exposes trusted results through a REST API.

---

## Current Status

**Architecture Complete (Phase 1).**

The platform architecture, abstractions, interfaces, documentation, and project skeleton are fully designed and implemented. Business logic and cloud integrations are scoped for Phase 2.

The following is complete:

- System architecture and module decomposition
- Repository structure and project skeleton
- Abstract interfaces for storage backends (ADR-005)
- Exception hierarchy across all layers
- Centralized configuration (Pydantic Settings)
- Circuit Breaker implementation with state machine
- FastAPI application scaffold with versioned routes
- Dagster orchestration scaffold with workspace configuration
- Docker Compose setup (API, Dagster webserver, Dagster daemon, Postgres)
- Test infrastructure (60 unit tests, CI configuration)
- Architecture documentation and decision records (ADR-001 through ADR-007)

---

## Purpose

Data pipelines that consume data from multiple external sources face three problems that this platform addresses:

1. **Source reliability.** External APIs fail, degrade, or produce conflicting data. The platform detects failures via Circuit Breaker, fails over between sources, and computes trust scores to quantify data reliability before it reaches consumers.
2. **Data quality at scale.** Raw data is never trusted. Every record passes through validation, normalization, deduplication, and business rule enforcement. Failed records are quarantined for reprocessing instead of being dropped silently.
3. **Observability.** Every decision, transformation, and data movement is logged and metered. The platform records why a source was chosen, how trust was computed, and what happened to every record.

---

## Design Principles

- **Immutable Raw Data** — Data in the Bronze layer is never modified or deleted.
- **Quarantine over Deletion** — Failed records are preserved for reprocessing instead of being dropped.
- **Separation of Concerns** — Decision Engine and Trust Layer are independent modules with distinct responsibilities.
- **Storage Isolation** — Business logic never depends on a specific storage backend (ADR-005).
- **API as Entry Point** — The REST API is the only external interface to trusted data (ADR-006).

---

## High-Level Architecture

```
Sources / DataStandardization          — Ingest and normalize data from external APIs
CoreETL (Bronze / Silver / Gold)       — Medallion Architecture pipeline
DataTrust                               — Evaluate data quality, reconcile sources, score confidence
DecisionEngine                          — Select sources, trip circuit breakers, trigger failover
Storage (S3 / BigQuery / SQLite)       — Persistence layer with abstract interfaces
API                                     — FastAPI-based REST entry point (ADR-006)
Observability                           — Logs, metrics, decision history, alerts, reports
Orchestration                           — Dagster asset definitions, jobs, schedules
Config                                  — Pydantic Settings, environment variable management, YAML policies
```

Detailed architecture documentation: `Docs/architecture.md`

---

## Technology Stack

### Core Technologies
- Python 3.9+
- FastAPI + Uvicorn
- Dagster
- Pandas, PyArrow
- Pydantic
- SQLite (development)
- structlog
- Docker Compose
- pytest

### Planned Integrations
- Apache Beam
- Amazon S3
- Google BigQuery

---

## Repository Structure

```
API/                    FastAPI application, route handlers, Pydantic schemas
Config/                 Centralized settings (Pydantic BaseSettings, env file loading)
CoreETL/                ETL pipeline: BronzeRAW, Silver, GoldTrusted, Quarantine, StateManager, Warehouse
  Pipeline/ApacheBeam/  Apache Beam pipeline (planned)
Dashboard/              Web UI (placeholder)
DataStandardization/    Schema mapping, normalization, validation
DataTrust/              Data quality, reconciliation, confidence scoring, LLM explainability
DecisionEngine/         Circuit Breaker, routing, failover, alerts, scheduling
Docs/                   Architecture documentation, ADRs
Observability/          Logs, metrics, alerts, decision history, routing history, reports
Orchestration/          Dagster assets, jobs, schedules, definitions
Sources/                Source connectors: PrimarySource, SecondSource, Common/Retry
Storage/                Backend abstractions: AmazonS3, GoogleBigQuery, SQLite
Tests/                  Unit and integration tests
```

---

## Development Roadmap

### Phase 1 — Architecture (complete)
- System architecture and documentation
- Abstract interfaces and project skeleton
- Configuration management and exception hierarchy
- Circuit Breaker implementation
- Test infrastructure

### Phase 2 — Implementation (in progress)
- Source adapters
- Apache Beam pipeline
- Cloud integrations
- Core ETL pipeline (Bronze ingestion, Silver validation, Gold aggregation)
- DataTrust scoring algorithms
- Decision Engine routing and failover
- API business logic

### Phase 3 — Production hardening (planned)
- Monitoring dashboards and alerting
- Performance optimization and benchmarking
- Deployment automation
- Load testing and scaling

---

## Project Progress

- **Phase 1 (Architecture)** — complete. All abstractions, interfaces, documentation, project skeleton, and test infrastructure are in place.
- **Phase 2 (Implementation)** — in progress. Source adapters, Apache Beam pipeline, Core ETL, Trust scoring, Decision Engine routing, and API business logic are being implemented.
- **Phase 3 (Production hardening)** — planned. Monitoring, performance optimization, and deployment automation are scoped for future work.

---

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pytest
docker compose up --build
```

---

## License

MIT License. See `LICENSE` for details.
