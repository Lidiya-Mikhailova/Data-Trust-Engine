from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

from DataStandardization.artifact import OperationType, OriginalValue, Transformation
from DataStandardization.schema import Schema


@dataclass(frozen=True)
class NormalizationRule:
    field: str
    operation: str
    params: Tuple[Any, ...] = ()


@dataclass(frozen=True)
class _OperationSpec:
    apply: Callable[[Tuple[Any, ...], Any], Any]
    reversible: bool
    inverse: Optional[Callable[[Tuple[Any, ...], Any], Any]] = None


def _collapse_whitespace(_params: Tuple[Any, ...], value: Any) -> Any:
    return " ".join(str(value).split())


def _trim(_params: Tuple[Any, ...], value: Any) -> Any:
    return str(value).strip()


def _casefold(_params: Tuple[Any, ...], value: Any) -> Any:
    return str(value).casefold()


def _strip_prefix(params: Tuple[Any, ...], value: Any) -> Any:
    prefix = str(params[0])
    text = str(value)
    return text[len(prefix) :] if text.startswith(prefix) else text


def _prepend_prefix(params: Tuple[Any, ...], value: Any) -> Any:
    return str(params[0]) + str(value)


def _strip_suffix(params: Tuple[Any, ...], value: Any) -> Any:
    suffix = str(params[0])
    text = str(value)
    return text[: -len(suffix)] if text.endswith(suffix) else text


def _append_suffix(params: Tuple[Any, ...], value: Any) -> Any:
    return str(value) + str(params[0])


def _reformat_date(params: Tuple[Any, ...], value: Any) -> Any:
    source_format, target_format = params
    return datetime.strptime(str(value), source_format).strftime(target_format)


def _reformat_date_inverse(params: Tuple[Any, ...], value: Any) -> Any:
    source_format, target_format = params
    return datetime.strptime(str(value), target_format).strftime(source_format)


OPERATIONS: Dict[str, _OperationSpec] = {
    "collapse_whitespace": _OperationSpec(_collapse_whitespace, reversible=False),
    "trim": _OperationSpec(_trim, reversible=False),
    "casefold": _OperationSpec(_casefold, reversible=False),
    "strip_prefix": _OperationSpec(_strip_prefix, reversible=True, inverse=_prepend_prefix),
    "strip_suffix": _OperationSpec(_strip_suffix, reversible=True, inverse=_append_suffix),
    "reformat_date": _OperationSpec(_reformat_date, reversible=True, inverse=_reformat_date_inverse),
}


class Normalizer:
    def __init__(self, schema: Schema, rules: Tuple[NormalizationRule, ...]) -> None:
        self._schema = schema
        self._rules = rules

    def normalize(
        self, record: Mapping[str, Any]
    ) -> Tuple[Dict[str, Any], Tuple[Transformation, ...]]:
        output = dict(record)
        transformations: list[Transformation] = []
        for rule in self._rules:
            spec = self._schema.resolve(rule.field)
            if spec is None:
                raise ValueError(f"normalization rule targets unknown field: {rule.field!r}")
            operation = OPERATIONS.get(rule.operation)
            if operation is None:
                raise ValueError(f"unknown normalization operation: {rule.operation!r}")
            field = spec.canonical_name
            if field not in output:
                continue
            normalized = operation.apply(rule.params, output[field])
            if normalized == output[field]:
                continue
            if operation.reversible:
                transformations.append(
                    Transformation(
                        operation_type=OperationType.REVERSIBLE,
                        operation=rule.operation,
                        field=field,
                        rule=rule.params,
                    )
                )
            else:
                transformations.append(
                    Transformation(
                        operation_type=OperationType.LOSSY,
                        operation=rule.operation,
                        field=field,
                        before=OriginalValue(output[field]),
                        after=normalized,
                    )
                )
            output[field] = normalized
        return output, tuple(transformations)
