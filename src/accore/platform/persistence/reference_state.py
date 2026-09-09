from __future__ import annotations

from collections.abc import (
    ItemsView,
    Iterator,
    KeysView,
    Mapping,
    ValuesView,
)
from types import MappingProxyType

from accore.platform.foundation.identity import Identifier

PersistentReferenceValue = Identifier | None | tuple[Identifier, ...]


class PersistentReferenceState(Mapping[str, PersistentReferenceValue]):
    """Immutable persistence-side state of durable references."""

    def __init__(
        self,
        values: Mapping[str, PersistentReferenceValue] | None = None,
    ) -> None:
        source = {} if values is None else dict(values)

        for name, value in source.items():
            self._validate_name(name)
            self._validate_value(value)

        self._values = MappingProxyType(source)

    @staticmethod
    def _validate_name(name: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Persistent reference name is required.")

    @staticmethod
    def _validate_value(value: PersistentReferenceValue) -> None:
        if value is None:
            return

        if isinstance(value, Identifier):
            return

        if not isinstance(value, tuple):
            raise TypeError(
                "Persistent reference value must be " "Identifier, None, or tuple[Identifier, ...]."
            )

        if not all(isinstance(identifier, Identifier) for identifier in value):
            raise TypeError("Persistent reference collection must contain only Identifier values.")

    @classmethod
    def empty(cls) -> PersistentReferenceState:
        return cls()

    def __getitem__(self, name: str) -> PersistentReferenceValue:
        return self._values[name]

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def keys(self) -> KeysView[str]:
        return self._values.keys()

    def values(self) -> ValuesView[PersistentReferenceValue]:
        return self._values.values()

    def items(self) -> ItemsView[str, PersistentReferenceValue]:
        return self._values.items()
