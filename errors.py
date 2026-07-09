class DataTrustEngineError(Exception):
    """Base exception for the entire project."""


class ConfigError(DataTrustEngineError):
    """Configuration loading or validation failed."""


class SourceError(DataTrustEngineError):
    """Base for data source connector errors."""


class SourceConnectionError(SourceError):
    """Cannot connect to external data source."""


class SourceParseError(SourceError):
    """Failed to parse data source response."""


class SourceRetryExhausted(SourceError):
    """All retry attempts to a data source failed."""


class DataStandardizationError(DataTrustEngineError):
    """Base for data standardization errors."""


class MappingError(DataStandardizationError):
    """Schema mapping between source and canonical failed."""


class ValidationError(DataStandardizationError):
    """Data validation failed during standardization."""


class NormalizationError(DataStandardizationError):
    """Data normalization failed."""


class ETLPipelineError(DataTrustEngineError):
    """Base for Core ETL pipeline errors."""


class BronzeIngestError(ETLPipelineError):
    """Raw data ingestion into Bronze failed."""


class BronzeIncrementalError(BronzeIngestError):
    """Incremental load into Bronze failed."""


class BronzeRecoveryError(BronzeIngestError):
    """Recovery of Bronze ingestion failed."""


class SilverProcessingError(ETLPipelineError):
    """Silver layer processing failed."""


class SilverDeduplicationError(SilverProcessingError):
    """Deduplication in Silver layer failed."""


class GoldProcessingError(ETLPipelineError):
    """Gold layer processing failed."""


class GoldBusinessRuleError(GoldProcessingError):
    """Business rule application in Gold layer failed."""


class GoldAggregationError(GoldProcessingError):
    """Aggregation in Gold layer failed."""


class GoldEnrichmentError(GoldProcessingError):
    """Enrichment in Gold layer failed."""


class QuarantineError(ETLPipelineError):
    """Base for Quarantine operations."""


class QuarantineStorageError(QuarantineError):
    """Failed to store or retrieve quarantined records."""


class QuarantineReprocessError(QuarantineError):
    """Reprocessing of quarantined records failed."""


class StateManagerError(ETLPipelineError):
    """State/checkpoint management failed."""


class CheckpointError(StateManagerError):
    """Checkpoint read or write failed."""


class StorageError(DataTrustEngineError):
    """Base for storage layer errors (ADR-005)."""


class DataLakeError(StorageError):
    """Data Lake (S3) operation failed."""


class DataLakeWriteError(DataLakeError):
    """Write to Data Lake failed."""


class DataLakeReadError(DataLakeError):
    """Read from Data Lake failed."""


class WarehouseError(StorageError):
    """Warehouse (BigQuery) operation failed."""


class WarehouseLoadError(WarehouseError):
    """Load into warehouse failed."""


class WarehouseQueryError(WarehouseError):
    """Query against warehouse failed."""


class ObservabilityDBError(StorageError):
    """Observability DB (SQLite) operation failed."""


class TrustError(DataTrustEngineError):
    """Base for Data Trust layer errors."""


class DataQualityError(TrustError):
    """Data quality check failed."""


class AnomalyDetectionError(DataQualityError):
    """Anomaly detection failed."""


class ReconciliationError(TrustError):
    """Cross-source reconciliation failed."""


class ConsensusError(ReconciliationError):
    """Consensus building across sources failed."""


class ConfidenceError(TrustError):
    """Confidence score computation failed."""


class LLMExplainabilityError(TrustError):
    """LLM-based explanation generation failed."""


class DecisionError(DataTrustEngineError):
    """Base for Decision Engine errors."""


class CircuitBreakerError(DecisionError):
    """Circuit breaker operation failed."""


class CircuitBreakerTripped(CircuitBreakerError):
    """Circuit breaker is open — source is unavailable."""


class FailoverError(DecisionError):
    """Failover between sources failed."""


class RoutingError(DecisionError):
    """Data routing decision failed."""


class SchedulingError(DecisionError):
    """Scheduling operation failed."""


class AlertError(DecisionError):
    """Alert generation or dispatch failed."""


class APIError(DataTrustEngineError):
    """Base for API layer errors."""


class APINotFoundError(APIError):
    """Requested resource not found."""


class APIValidationError(APIError):
    """Request validation failed."""


class APIAuthenticationError(APIError):
    """Authentication failed."""


class ObservabilityError(DataTrustEngineError):
    """Base for Observability layer errors."""


class MetricCollectionError(ObservabilityError):
    """Metric collection or emission failed."""


class NotificationError(ObservabilityError):
    """Notification dispatch failed."""


class ReportGenerationError(ObservabilityError):
    """Report generation failed."""


class LoggingError(ObservabilityError):
    """Logging infrastructure error."""


class OrchestrationError(DataTrustEngineError):
    """Base for orchestration (Dagster) errors."""


class DagsterAssetError(OrchestrationError):
    """Dagster asset execution failed."""


class DagsterJobError(OrchestrationError):
    """Dagster job execution failed."""
