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

---

## ADR-008

Data standardization is reversible and lineage-aware.

Reason:

Raw records must be mapped to a canonical schema (aliases to canonical field names) and normalized (whitespace, case, prefix/suffix, date format). Every applied transformation is recorded on a `CanonicalArtifact` as either reversible (rule-based, e.g. strip prefix/suffix, date reformat) or lossy (value snapshot kept in `before`, e.g. trim, casefold). This allows reconstructing the original record for audit and replay while keeping downstream layers on a stable canonical shape. Validation stays separate from transformation: the Validator only reports errors/warnings and never mutates the record.

---
