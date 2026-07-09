# Architecture Decision Records

## ADR-001

Each data source has its own Dagster asset / job.

Reason:

Different schedules and independent retries. Using Dagster's software-defined assets gives built-in data lineage per source.

---

## ADR-002

Raw data is immutable.

Reason:

Allows replay and debugging.

---

## ADR-003

Failed records are moved to Quarantine instead of being deleted.

Reason:

Preserves data lineage.

---

## ADR-004

Decision Engine and Trust Layer are separated.

Reason:

Validation and routing have different responsibilities.

---

## ADR-005

Storage is isolated from business logic.

Reason:

Allows replacing storage backends without changing ETL logic.

---

## ADR-006

API is the only external entry point.

Reason:

Provides controlled access to trusted data.

---

## ADR-007

Dagster is the orchestration framework.

Reason:

Airflow was initially considered, but Dagster was chosen for its asset-based programming model, native software-defined assets, better developer experience for data pipelines, and first-class support for data lineage and observability. Dagster's asset graph aligns well with the Medallion Architecture (Bronze → Silver → Gold).