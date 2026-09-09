from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from datetime import date, datetime
from decimal import Decimal
from typing import TypeGuard, overload


class DurableValueError(ValueError):
    """Raised when a value violates the durable-value contract."""


class StructuredValue:
    """Immutable semantic mapping from field identity to durable value."""

    __slots__ = ("_items",)

    def __init__(
        self,
        values: Mapping[str, DurableValue] | Iterable[tuple[str, DurableValue]],
    ) -> None:
        if isinstance(values, Mapping):
            items: Iterable[tuple[str, DurableValue]] = values.items()
        else:
            items = values

        normalized: list[tuple[str, DurableValue]] = []
        seen: set[str] = set()
        for key, value in items:
            if type(key) is not str or not key.strip():
                raise DurableValueError("Structured value keys must be non-empty strings.")
            if key in seen:
                raise DurableValueError(f"Duplicate structured value key: {key!r}.")
            validate_durable_value(value)
            seen.add(key)
            normalized.append((key, value))

        self._items = tuple(sorted(normalized, key=lambda item: item[0]))

    def __getitem__(self, key: str) -> DurableValue:
        for field_name, value in self._items:
            if field_name == key:
                return value
        raise KeyError(key)

    def get(self, key: str, default: DurableValue | None = None) -> DurableValue | None:
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key: object) -> bool:
        return any(field_name == key for field_name, _ in self._items)

    def __iter__(self) -> Iterator[str]:
        return (field_name for field_name, _ in self._items)

    def __len__(self) -> int:
        return len(self._items)

    def keys(self) -> tuple[str, ...]:
        return tuple(field_name for field_name, _ in self._items)

    def values(self) -> tuple[DurableValue, ...]:
        return tuple(value for _, value in self._items)

    def items(self) -> tuple[tuple[str, DurableValue], ...]:
        return self._items

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StructuredValue):
            return NotImplemented
        return self._items == other._items

    def __hash__(self) -> int:
        return hash(self._items)

    def __repr__(self) -> str:
        return f"StructuredValue({dict(self._items)!r})"


class CollectionValue:
    """Immutable ordered sequence of durable values."""

    __slots__ = ("_values",)

    def __init__(self, values: Iterable[DurableValue]) -> None:
        normalized = tuple(values)
        for value in normalized:
            validate_durable_value(value)
        self._values = normalized

    @overload
    def __getitem__(self, index: int) -> DurableValue: ...

    @overload
    def __getitem__(self, index: slice) -> CollectionValue: ...

    def __getitem__(self, index: int | slice) -> DurableValue | CollectionValue:
        if isinstance(index, slice):
            return CollectionValue(self._values[index])
        return self._values[index]

    def __iter__(self) -> Iterator[DurableValue]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __contains__(self, value: object) -> bool:
        return value in self._values

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CollectionValue):
            return NotImplemented
        return self._values == other._values

    def __hash__(self) -> int:
        return hash(self._values)

    def __repr__(self) -> str:
        return f"CollectionValue({self._values!r})"


type DurableScalar = bool | int | Decimal | str | date | datetime
type DurableValue = DurableScalar | StructuredValue | CollectionValue


def is_durable_value(value: object) -> TypeGuard[DurableValue]:
    """Return whether ``value`` satisfies the Step 12 durable-value contract."""

    if type(value) in (bool, int, Decimal, str, date, datetime):
        return True

    if isinstance(value, StructuredValue):
        return all(is_durable_value(item_value) for _, item_value in value.items())

    if isinstance(value, CollectionValue):
        return all(is_durable_value(item) for item in value)

    return False


def validate_durable_value(value: object) -> None:
    """Validate a value against the Step 12 durable-value contract."""

    if is_durable_value(value):
        return

    raise DurableValueError(
        f"Unsupported durable value type: {type(value).__module__}.{type(value).__qualname__}."
    )
