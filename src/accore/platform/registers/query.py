from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import TYPE_CHECKING, Protocol

from accore.platform.foundation import Identifier
from accore.platform.registers.movement import Movement, MovementScalar

if TYPE_CHECKING:
    from accore.platform.persistence.facts import RegisterFactPersistence


class MovementQueryValidationError(ValueError):
    """Raised when Movement Query input violates semantic invariants."""


@dataclass(frozen=True, slots=True)
class MovementQueryPeriod:
    """Immutable half-open period used by Movement Query."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start.tzinfo is None or self.start.utcoffset() is None:
            raise MovementQueryValidationError("Movement query period start must be timezone-aware")
        if self.end.tzinfo is None or self.end.utcoffset() is None:
            raise MovementQueryValidationError("Movement query period end must be timezone-aware")
        if self.start >= self.end:
            raise MovementQueryValidationError("Movement query period requires start < end")


@dataclass(frozen=True, slots=True)
class MovementDimensionFilter:
    """Immutable partial filter over Movement dimensions."""

    values: Mapping[str, MovementScalar]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, MovementScalar],
    ) -> MovementDimensionFilter:
        return cls(values)


@dataclass(frozen=True, slots=True)
class MovementQuery:
    """Immutable semantic query for persisted Register Movement facts."""

    register_identity: Identifier
    period: MovementQueryPeriod
    dimensions: MovementDimensionFilter


class MovementQueryService(Protocol):
    """Public semantic boundary for Movement queries."""

    def query(self, query: MovementQuery) -> tuple[Movement, ...]:
        """Return persisted movements matching the semantic query."""


class DefaultMovementQueryService:
    """Reference Movement Query implementation over Register fact persistence."""

    def __init__(self, persistence: RegisterFactPersistence) -> None:
        self._persistence = persistence

    def query(self, query: MovementQuery) -> tuple[Movement, ...]:
        movements = self._persistence.enumerate(query.register_identity)
        matching = (
            movement
            for movement in movements
            if self._matches_period(movement, query.period)
            and self._matches_dimensions(movement, query.dimensions)
        )
        return tuple(
            sorted(
                matching,
                key=lambda movement: (movement.accounting_time, str(movement.identity)),
            )
        )

    @staticmethod
    def _matches_period(
        movement: Movement,
        period: MovementQueryPeriod,
    ) -> bool:
        accounting_time = movement.accounting_time
        return accounting_time is not None and period.start <= accounting_time < period.end

    @staticmethod
    def _matches_dimensions(
        movement: Movement,
        dimensions: MovementDimensionFilter,
    ) -> bool:
        missing = object()
        for key, expected in dimensions.values.items():
            actual = movement.dimensions.get(key, missing)
            if actual is missing or actual != expected:
                return False
        return True
