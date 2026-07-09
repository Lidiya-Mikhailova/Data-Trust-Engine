from __future__ import annotations

from Storage.interfaces import AbstractDataLake, AbstractWarehouse, AbstractObservabilityDB


class TestAbstractDataLake:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            AbstractDataLake()  # type: ignore


class TestAbstractWarehouse:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            AbstractWarehouse()  # type: ignore


class TestAbstractObservabilityDB:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            AbstractObservabilityDB()  # type: ignore


import pytest  # noqa: E402 (isort split)
