from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple


@dataclass(frozen=True)
class FieldSpec:
    canonical_name: str
    value_type: Optional[type] = None
    required: bool = False
    aliases: Tuple[str, ...] = ()
    allowed_values: Optional[Tuple[Any, ...]] = None


class Schema:
    def __init__(self, fields: Iterable[FieldSpec]) -> None:
        self._fields: Tuple[FieldSpec, ...] = tuple(fields)
        self._lookup: Dict[str, FieldSpec] = {}
        for field in self._fields:
            self._lookup[field.canonical_name] = field
            for alias in field.aliases:
                self._lookup[alias] = field

    @property
    def fields(self) -> Tuple[FieldSpec, ...]:
        return self._fields

    def resolve(self, name: str) -> Optional[FieldSpec]:
        return self._lookup.get(name)
