from __future__ import annotations

from typing import Any, Dict, Mapping, Tuple

from DataStandardization.artifact import OperationType, Transformation
from DataStandardization.schema import Schema


class FieldMapper:
    def __init__(self, schema: Schema) -> None:
        self._schema = schema

    def apply(self, record: Mapping[str, Any]) -> Tuple[Dict[str, Any], Tuple[Transformation, ...]]:
        output: Dict[str, Any] = {}
        transformations: list[Transformation] = []
        for key, value in record.items():
            spec = self._schema.resolve(key)
            if spec is None:
                output[key] = value
                continue
            canonical = spec.canonical_name
            if canonical != key:
                output[canonical] = value
                transformations.append(
                    Transformation(
                        operation_type=OperationType.REVERSIBLE,
                        operation="rename_field",
                        field=canonical,
                        rule=(key,),
                    )
                )
            else:
                output[canonical] = value
        return output, tuple(transformations)

    def apply_inverse(self, record: Mapping[str, Any]) -> Dict[str, Any]:
        output: Dict[str, Any] = {}
        for key, value in record.items():
            spec = self._schema.resolve(key)
            if spec is None:
                output[key] = value
                continue
            if key == spec.canonical_name and spec.aliases:
                output[spec.aliases[0]] = value
            else:
                output[key] = value
        return output
