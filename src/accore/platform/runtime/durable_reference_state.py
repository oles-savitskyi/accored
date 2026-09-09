from __future__ import annotations

from collections.abc import (
    ItemsView,
    Iterator,
    KeysView,
    Mapping,
    ValuesView,
)
from types import MappingProxyType
from typing import Any, Self

from accore.platform.foundation.identity import Identifier
from accore.platform.value.durable import DurableValueError

ReferenceValue = Identifier | None | tuple[Identifier, ...]


class DurableReferenceState:
    """Immutable runtime representation of durable object references.

    Reference identities are canonical Metadata reference names in the
    current Metadata model.

    A reference value may be:

    * ``ObjectIdentity`` — a SINGLE reference;
    * ``None`` — explicit NULL for a SINGLE reference;
    * ``tuple[ObjectIdentity, ...]`` — a MANY reference.

    The distinction between SINGLE and MANY is defined by Metadata and is
    intentionally not interpreted by this container.

    Absence of a key represents MISSING.
    """

    __slots__ = ("_values",)

    def __init__(
        self,
        values: Mapping[str, ReferenceValue],
    ) -> None:
        snapshot: dict[str, ReferenceValue] = {}

        for key, value in values.items():
            self._validate_reference_identity(key)
            snapshot[key] = self._validate_reference_value(key, value)

        self._values = MappingProxyType(snapshot)

    @classmethod
    def empty(cls) -> Self:
        """Create an empty durable reference state."""
        return cls({})

    @staticmethod
    def _validate_reference_identity(key: Any) -> None:
        if not isinstance(key, str):
            raise DurableValueError(f"Reference identity must be str, got {type(key).__name__}")

        if not key.strip():
            raise DurableValueError("Reference identity must not be empty or whitespace-only")

    @staticmethod
    def _validate_reference_value(
        key: str,
        value: ReferenceValue,
    ) -> ReferenceValue:
        if value is None:
            return None

        if isinstance(value, Identifier):
            return value

        if isinstance(value, tuple):
            for identity in value:
                if not isinstance(identity, Identifier):
                    raise DurableValueError(f"Reference {key!r} contains an invalid ObjectIdentity")

            return value

        raise DurableValueError(f"Reference {key!r} contains an invalid reference value")

    def __getitem__(self, key: str) -> ReferenceValue:
        return self._values[key]

    def get(
        self,
        key: str,
        default: ReferenceValue = None,
    ) -> ReferenceValue:
        return self._values.get(key, default)

    def __contains__(self, key: object) -> bool:
        return key in self._values

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def keys(self) -> KeysView[str]:
        return self._values.keys()

    def values(self) -> ValuesView[ReferenceValue]:
        return self._values.values()

    def items(self) -> ItemsView[str, ReferenceValue]:
        return self._values.items()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DurableReferenceState):
            return NotImplemented

        return self._values == other._values

    def __repr__(self) -> str:
        return f"DurableReferenceState({dict(self._values)!r})"
