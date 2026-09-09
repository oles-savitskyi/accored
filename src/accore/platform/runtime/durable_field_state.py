from __future__ import annotations

from collections.abc import ItemsView, Iterator, KeysView, Mapping, ValuesView
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Self

from accore.platform.value.durable import DurableValueError, is_durable_value

if TYPE_CHECKING:
    from accore.platform.value.durable import DurableValue


class DurableFieldState:
    """Immutable runtime representation of durable field values.

    Field identities are canonical Metadata field names in the current
    Metadata model. The container owns a defensive snapshot of the supplied
    mapping and exposes read-only Mapping semantics.

    ``None`` represents an explicit durable NULL value.
    Absence of a key represents MISSING.
    """

    __slots__ = ("_values",)

    def __init__(
        self,
        values: Mapping[str, DurableValue | None],
    ) -> None:
        snapshot: dict[str, DurableValue | None] = {}

        for key, value in values.items():
            self._validate_field_identity(key)

            if value is not None and not is_durable_value(value):
                raise DurableValueError(
                    f"Field {key!r} contains a value that is not " "a valid DurableValue"
                )

            snapshot[key] = value

        self._values = MappingProxyType(snapshot)

    @classmethod
    def empty(cls) -> Self:
        """Create an empty durable field state."""
        return cls({})

    @staticmethod
    def _validate_field_identity(key: Any) -> None:
        if not isinstance(key, str):
            raise DurableValueError(f"Field identity must be str, got {type(key).__name__}")

        if not key.strip():
            raise DurableValueError("Field identity must not be empty or whitespace-only")

    def __getitem__(
        self,
        key: str,
    ) -> DurableValue | None:
        return self._values[key]

    def get(
        self,
        key: str,
        default: DurableValue | None = None,
    ) -> DurableValue | None:
        return self._values.get(key, default)

    def __contains__(self, key: object) -> bool:
        return key in self._values

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def keys(self) -> KeysView[str]:
        return self._values.keys()

    def values(self) -> ValuesView[DurableValue | None]:
        return self._values.values()

    def items(self) -> ItemsView[str, DurableValue | None]:
        return self._values.items()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DurableFieldState):
            return NotImplemented

        return self._values == other._values

    def __repr__(self) -> str:
        return f"DurableFieldState({dict(self._values)!r})"
