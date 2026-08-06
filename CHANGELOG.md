# Changelog

## [0.3.0] - 2026-08-06

### Added

- **ADR-008**: Data standardization is reversible and lineage-aware
- **DataStandardization module**: canonical schema (`FieldSpec`/`Schema`) with aliases, `FieldMapper`, `Normalizer` (whitespace, trim, casefold, prefix/suffix, date reformat), `Validator`, and `standardize()` entry point producing a `CanonicalArtifact` that records reversible/lossy transformations for exact original-record reconstruction
- **Tests**: 34 unit tests for DataStandardization (100% module coverage)

### Changed

- **requirements.txt**: removed unused runtime deps (pandas, pyarrow, sqlalchemy, requests, python-dotenv) that are not imported anywhere in source; production file now contains only dependencies required by the application
- **requirements-dev.txt**: new file for test and lint tooling (pytest family, httpx, ruff)
- **CI**: both `lint` and `test` jobs now install `-r requirements.txt -r requirements-dev.txt`

## [0.2.0] - 2026-07-09

### Added

- **ADR-007**: Dagster chosen as orchestration framework (replaces Airflow)
- **Orchestration**: Dagster workspace config (`workspace.yaml`), docker-compose services (webserver, daemon, postgres), Dockerfile target
- **Config module**: Pydantic v2 Settings with `AppSettings`, `LogSettings`, `S3Settings`, `BigQuerySettings`, `SQLiteSettings`; env var mapping via validation_alias
- **Storage isolation (ADR-005)**: Abstract interfaces (`AbstractDataLake`, `AbstractWarehouse`, `AbstractObservabilityDB`) in `Storage/interfaces.py`; concrete stubs for S3, BigQuery, SQLite
- **Exception hierarchy**: `errors.py` with 40+ exception classes covering all layers (Config, Sources, ETL, Storage, Trust, DecisionEngine, API, Observability, Orchestration)
- **Circuit Breaker**: Full state machine (CLOSED/OPEN/HALF_OPEN) with sync `call()` and `async_call()`, configurable thresholds and timeout, proper error propagation
- **Test scaffold**: pytest + asyncio + cov config, global fixtures (mock clients, sample data), 60 tests across all modules (errors, config, storage interfaces, circuit breaker, API routes)
- **FastAPI application**: `API/main.py` with CORS, lifespan, versioned routes (`/api/v1`); routers for Health, Sources, ETL, Trust, Decisions, Data; Pydantic request/response schemas

### Changed

- **ADR-001**: Updated from Airflow DAG to Dagster asset/job
- **Dockerfile**: `airflow` target replaced with `dagster` (CMD: `dagster-webserver`)
- **docker-compose.yml**: Orchestration services added (dagster, dagster_daemon, dagster_postgres)
- **requirements.txt**: Added pydantic-settings, dagster, dagster-webserver, dagster-postgres, pytest, pytest-asyncio, pytest-cov, pytest-mock, httpx
- **`.env.example`**: Removed Airflow vars, added Dagster + SQLite vars
- **`Orchestration/dagster/difinitions.py`**: Renamed to `definitions.py` (fixed typo)