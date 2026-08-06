from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Tuple

from DataStandardization.schema import Schema


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    errors: Tuple[str, ...]
    warnings: Tuple[str, ...]


class Validator:
    def __init__(self, schema: Schema) -> None:
        self._schema = schema

    def validate(self, record: Mapping[str, Any]) -> ValidationReport:
        resolved: Dict[str, Any] = {}
        warnings: list[str] = []
        for key, value in record.items():
            spec = self._schema.resolve(key)
            if spec is None:
                warnings.append(f"unknown field: {key}")
                continue
            resolved[spec.canonical_name] = value
        errors: list[str] = []
        for spec in self._schema.fields:
            canonical = spec.canonical_name
            if canonical not in resolved:
                if spec.required:
                    errors.append(f"missing required field: {canonical}")
                continue
            value = resolved[canonical]
            if value is None:
                if spec.required:
                    errors.append(f"required field is null: {canonical}")
                continue
            if spec.value_type is not None and not isinstance(value, spec.value_type):
                errors.append(
                    f"field {canonical}: expected {spec.value_type.__name__}, got {type(value).__name__}"
                )
            if spec.allowed_values is not None and value not in spec.allowed_values:
                errors.append(f"field {canonical}: value {value!r} not allowed")
        warnings.sort()
        return ValidationReport(valid=not errors, errors=tuple(errors), warnings=tuple(warnings))
