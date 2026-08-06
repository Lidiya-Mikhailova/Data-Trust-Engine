from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional, Tuple


class OperationType(Enum):
    REVERSIBLE = "reversible"
    LOSSY = "lossy"


@dataclass(frozen=True)
class OriginalValue:
    value: Any


@dataclass(frozen=True)
class Transformation:
    operation_type: OperationType
    operation: str
    field: str
    rule: Optional[Tuple[Any, ...]] = None
    before: Optional[OriginalValue] = None
    after: Optional[Any] = None

    def __post_init__(self) -> None:
        if self.operation_type is OperationType.REVERSIBLE and self.rule is None:
            raise ValueError("REVERSIBLE transformation requires a rule")
        if self.operation_type is OperationType.LOSSY and (
            not isinstance(self.before, OriginalValue) or self.after is None
        ):
            raise ValueError("LOSSY transformation requires before and after")


@dataclass(frozen=True)
class CanonicalArtifact:
    canonical_data: Mapping[str, Any]
    transformations: Tuple[Transformation, ...]
