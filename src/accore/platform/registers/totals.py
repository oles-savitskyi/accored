from __future__ import annotations

from collections.abc import ItemsView, Iterator, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import Protocol

from accore.platform.foundation import Identifier

from .movement import Movement, MovementScalar, MovementType

type TotalValue = Decimal


class TotalsError(ValueError):
    """Base error for Totals semantic failures."""


class TotalsDefinitionError(TotalsError):
    """Raised when Register totals configuration is invalid."""


class TotalsAggregationError(TotalsError):
    """Raised when a Movement cannot be aggregated according to Register semantics."""


class TotalsRegisterMismatchError(TotalsAggregationError):
    """Raised when a Movement belongs to another Register."""


class TotalsKeyError(TotalsAggregationError):
    """Raised when a Movement cannot produce the configured TotalsKey."""


class TotalsResourceError(TotalsAggregationError):
    """Raised when a Movement resource is missing or has an invalid type."""


class TotalsMovementTypeError(TotalsAggregationError):
    """Raised when MovementType has no configured accounting effect."""


@dataclass(frozen=True, slots=True)
class TotalsKey:
    """Immutable semantic aggregation key owned by the Totals Engine."""

    _values: tuple[tuple[str, MovementScalar], ...]

    @classmethod
    def from_mapping(cls, values: Mapping[str, MovementScalar]) -> TotalsKey:
        normalized = tuple(sorted(values.items(), key=lambda item: item[0]))
        for name, value in normalized:
            if not name:
                raise TotalsKeyError("TotalsKey dimension names must be non-empty.")
            try:
                hash(value)
            except TypeError as exc:
                raise TotalsKeyError(
                    f"TotalsKey dimension '{name}' must contain a hashable value."
                ) from exc
        return cls(normalized)

    @property
    def values(self) -> Mapping[str, MovementScalar]:
        return MappingProxyType(dict(self._values))

    def get(self, key: str, default: MovementScalar | None = None) -> MovementScalar | None:
        return dict(self._values).get(key, default)

    def __getitem__(self, key: str) -> MovementScalar:
        for name, value in self._values:
            if name == key:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return (name for name, _ in self._values)

    def __len__(self) -> int:
        return len(self._values)

    def items(self) -> ItemsView[str, MovementScalar]:
        return self.values.items()


@dataclass(frozen=True, slots=True)
class TotalsDefinition:
    """Register-defined semantics required to aggregate Movement facts."""

    register_identity: Identifier
    dimensions: tuple[str, ...]
    resource_name: str
    movement_type_signs: Mapping[MovementType, int]
    resource_type: type[Decimal] = Decimal

    def __post_init__(self) -> None:
        if not self.dimensions:
            raise TotalsDefinitionError("TotalsDefinition requires at least one dimension.")
        if len(set(self.dimensions)) != len(self.dimensions):
            raise TotalsDefinitionError("TotalsDefinition dimensions must be unique.")
        if any(not name for name in self.dimensions):
            raise TotalsDefinitionError("TotalsDefinition dimension names must be non-empty.")
        if not self.resource_name:
            raise TotalsDefinitionError("TotalsDefinition resource_name must be non-empty.")
        if self.resource_type is not Decimal:
            raise TotalsDefinitionError(
                "Phase 7 Totals currently aggregates Decimal resources only."
            )
        signs = dict(self.movement_type_signs)
        if not signs:
            raise TotalsDefinitionError("TotalsDefinition requires MovementType semantics.")
        if any(sign not in (-1, 1) for sign in signs.values()):
            raise TotalsDefinitionError("MovementType contribution signs must be -1 or 1.")
        object.__setattr__(self, "movement_type_signs", MappingProxyType(signs))

    def key_for(self, movement: Movement) -> TotalsKey:
        if movement.register_identity != self.register_identity:
            raise TotalsRegisterMismatchError("Movement does not belong to the Totals Register.")

        values: dict[str, MovementScalar] = {}
        for dimension in self.dimensions:
            value = movement.dimensions.get(dimension)
            if value is None:
                raise TotalsKeyError(
                    f"Movement is missing required aggregation dimension '{dimension}'."
                )
            values[dimension] = value
        return TotalsKey.from_mapping(values)

    def contribution_for(self, movement: Movement) -> TotalValue:
        sign = self.movement_type_signs.get(movement.movement_type)
        if sign is None:
            raise TotalsMovementTypeError(
                f"MovementType '{movement.movement_type}' has no configured totals effect."
            )

        value = movement.resources.get(self.resource_name)
        if value is None:
            raise TotalsResourceError(
                f"Movement is missing required resource '{self.resource_name}'."
            )
        if not isinstance(value, self.resource_type):
            raise TotalsResourceError(
                f"Resource '{self.resource_name}' must be {self.resource_type.__name__}."
            )
        if value <= 0:
            raise TotalsResourceError(
                f"Resource '{self.resource_name}' must be a positive magnitude."
            )
        return value if sign > 0 else -value


class TotalsReader(Protocol):
    """Read boundary for the currently established derived Totals state."""

    def get(self, register_identity: Identifier, key: TotalsKey) -> TotalValue:
        """Return the current total for one Register aggregation key."""


class TotalsEngine(TotalsReader, Protocol):
    """Semantic Totals Engine boundary."""

    def apply(self, movement: Movement) -> TotalValue:
        """Apply one Movement contribution."""

    def remove(self, movement: Movement) -> TotalValue:
        """Remove one Movement contribution."""

    def rebuild(self, register_identity: Identifier, movements: Sequence[Movement]) -> None:
        """Rebuild one Register from the supplied authoritative Movement facts."""


class DefaultTotalsEngine:
    """In-memory reference Totals Engine for the Phase 7 semantic contract."""

    def __init__(self, definitions: Sequence[TotalsDefinition]) -> None:
        self._definitions = {definition.register_identity: definition for definition in definitions}
        if len(self._definitions) != len(definitions):
            raise TotalsDefinitionError("Totals definitions must have unique Register identities.")
        self._totals: dict[Identifier, dict[TotalsKey, TotalValue]] = {
            register_identity: {} for register_identity in self._definitions
        }

    def get(self, register_identity: Identifier, key: TotalsKey) -> TotalValue:
        self._definition(register_identity)
        return self._totals[register_identity].get(key, Decimal(0))

    def apply(self, movement: Movement) -> TotalValue:
        definition = self._definition(movement.register_identity)
        key = definition.key_for(movement)
        contribution = definition.contribution_for(movement)
        register_totals = self._totals[movement.register_identity]
        value = register_totals.get(key, Decimal(0)) + contribution
        if value == 0:
            register_totals.pop(key, None)
        else:
            register_totals[key] = value
        return value

    def remove(self, movement: Movement) -> TotalValue:
        definition = self._definition(movement.register_identity)
        key = definition.key_for(movement)
        contribution = definition.contribution_for(movement)
        register_totals = self._totals[movement.register_identity]
        value = register_totals.get(key, Decimal(0)) - contribution
        if value == 0:
            register_totals.pop(key, None)
        else:
            register_totals[key] = value
        return value

    def rebuild(self, register_identity: Identifier, movements: Sequence[Movement]) -> None:
        definition = self._definition(register_identity)
        replacement: dict[TotalsKey, TotalValue] = {}
        for movement in movements:
            key = definition.key_for(movement)
            contribution = definition.contribution_for(movement)
            replacement[key] = replacement.get(key, Decimal(0)) + contribution
        replacement = {key: value for key, value in replacement.items() if value != 0}
        self._totals[register_identity] = replacement

    def _definition(self, register_identity: Identifier) -> TotalsDefinition:
        try:
            return self._definitions[register_identity]
        except KeyError as exc:
            raise TotalsDefinitionError(
                f"No TotalsDefinition configured for Register '{register_identity}'."
            ) from exc
