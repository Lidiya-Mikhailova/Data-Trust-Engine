from __future__ import annotations

import pytest

from Storage.interfaces import DataLakeStorage, WarehouseStorage, ObservabilityStorage


class TestDataLakeStorage:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            DataLakeStorage()  # type: ignore


class TestWarehouseStorage:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            WarehouseStorage()  # type: ignore


class TestObservabilityStorage:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            ObservabilityStorage()  # type: ignore
