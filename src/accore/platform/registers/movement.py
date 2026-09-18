from __future__ import annotations

from collections.abc import ItemsView, Iterator, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType

from accore.platform.foundation import Identifier

type MovementScalar = object


class MovementType(StrEnum):
    """Platform movement-type vocabulary currently required by Phase 6."""

    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class _ImmutableMapping:
    __slots__ = ("_values",)

    def __init__(self, values: Mapping[str, MovementScalar] | None = None) -> None:
        self._values = MappingProxyType(dict(values or {}))

    def __getitem__(self, key: str) -> MovementScalar:
        return self._values[key]

    def get(self, key: str, default: MovementScalar | None = None) -> MovementScalar | None:
        return self._values.get(key, default)

    def __contains__(self, key: object) -> bool:
        return key in self._values

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def items(self) -> ItemsView[str, MovementScalar]:
        return self._values.items()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _ImmutableMapping) and self._values == other._values

    def __repr__(self) -> str:
        return repr(dict(self._values))


@dataclass(frozen=True, slots=True)
class MovementDimensions:
    values: _ImmutableMapping

    @classmethod
    def from_mapping(cls, values: Mapping[str, MovementScalar]) -> MovementDimensions:
        return cls(_ImmutableMapping(values))

    def get(self, key: str, default: MovementScalar | None = None) -> MovementScalar | None:
        return self.values.get(key, default)


@dataclass(frozen=True, slots=True)
class MovementResources:
    values: _ImmutableMapping

    @classmethod
    def from_mapping(cls, values: Mapping[str, MovementScalar]) -> MovementResources:
        return cls(_ImmutableMapping(values))

    def get(self, key: str, default: MovementScalar | None = None) -> MovementScalar | None:
        return self.values.get(key, default)


@dataclass(frozen=True, slots=True)
class MovementAttributes:
    values: _ImmutableMapping

    @classmethod
    def from_mapping(cls, values: Mapping[str, MovementScalar]) -> MovementAttributes:
        return cls(_ImmutableMapping(values))

    def get(self, key: str, default: MovementScalar | None = None) -> MovementScalar | None:
        return self.values.get(key, default)


@dataclass(frozen=True, slots=True)
class Movement:
    """Immutable accounting fact accepted by a Register Posting Contract."""

    identity: Identifier
    source_document_identity: Identifier
    register_identity: Identifier
    movement_type: MovementType
    dimensions: MovementDimensions
    resources: MovementResources
    attributes: MovementAttributes
    accounting_time: datetime | None
