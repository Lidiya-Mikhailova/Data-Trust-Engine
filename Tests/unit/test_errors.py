from __future__ import annotations

from errors import (
    DataTrustEngineError,
    ConfigError,
    SourceConnectionError,
    SourceRetryExhausted,
    ETLPipelineError,
    BronzeIngestError,
    StorageError,
    DataLakeError,
    WarehouseError,
    TrustError,
    DecisionError,
    CircuitBreakerTripped,
    APIError,
    APINotFoundError,
)


class TestDataTrustEngineError:
    def test_is_base_exception(self):
        assert issubclass(DataTrustEngineError, Exception)

    def test_can_be_raised_with_message(self):
        err = DataTrustEngineError("something went wrong")
        assert str(err) == "something went wrong"


class TestConfigError:
    def test_inheritance(self):
        assert issubclass(ConfigError, DataTrustEngineError)


class TestSourceErrors:
    def test_source_connection_error_inheritance(self):
        assert issubclass(SourceConnectionError, DataTrustEngineError)

    def test_source_retry_exhausted_inheritance(self):
        assert issubclass(SourceRetryExhausted, DataTrustEngineError)


class TestPipelineErrors:
    def test_bronze_ingest_inheritance(self):
        assert issubclass(BronzeIngestError, ETLPipelineError)
        assert issubclass(ETLPipelineError, DataTrustEngineError)


class TestStorageErrors:
    def test_storage_hierarchy(self):
        assert issubclass(DataLakeError, StorageError)
        assert issubclass(WarehouseError, StorageError)
        assert issubclass(StorageError, DataTrustEngineError)


class TestTrustErrors:
    def test_trust_hierarchy(self):
        assert issubclass(TrustError, DataTrustEngineError)


class TestDecisionErrors:
    def test_circuit_breaker_tripped(self):
        err = CircuitBreakerTripped("source-x is down")
        assert "source-x" in str(err)
        assert issubclass(CircuitBreakerTripped, DecisionError)


class TestAPIErrors:
    def test_api_not_found(self):
        err = APINotFoundError("resource not found")
        assert "resource not found" in str(err)
        assert issubclass(APINotFoundError, APIError)
