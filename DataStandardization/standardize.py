from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping

from DataStandardization.artifact import CanonicalArtifact, OperationType
from DataStandardization.mapper import FieldMapper
from DataStandardization.normalizer import OPERATIONS, NormalizationRule, Normalizer
from DataStandardization.schema import Schema


def standardize(
    record: Mapping[str, Any],
    schema: Schema,
    rules: Iterable[NormalizationRule] = (),
) -> CanonicalArtifact:
    mapper = FieldMapper(schema)
    mapped, rename_transformations = mapper.apply(record)
    normalizer = Normalizer(schema, tuple(rules))
    normalized, normalize_transformations = normalizer.normalize(mapped)
    return CanonicalArtifact(
        canonical_data=normalized,
        transformations=rename_transformations + normalize_transformations,
    )


def reconstruct_original(artifact: CanonicalArtifact) -> Dict[str, Any]:
    output = dict(artifact.canonical_data)
    for transformation in reversed(artifact.transformations):
        if transformation.operation == "rename_field":
            original_name = transformation.rule[0]
            output[original_name] = output.pop(transformation.field)
        elif transformation.operation_type is OperationType.LOSSY:
            output[transformation.field] = transformation.before.value
        else:
            operation = OPERATIONS[transformation.operation]
            output[transformation.field] = operation.inverse(
                transformation.rule, output[transformation.field]
            )
    return output
