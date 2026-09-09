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
from accore.platform.value.durable import DurableValue, validate_durable_value

PersistentSystemFieldValue = DurableValue | Identifier | None


class PersistentSystemFieldState(Mapping[str, PersistentSystemFieldValue]):
    """Immutable persistence-side state of durable system fields."""

    def __init__(
        self,
        values: Mapping[str, PersistentSystemFieldValue] | None = None,
    ) -> None:
        source = {} if values is None else dict(values)

        for name, value in source.items():
            self._validate_name(name)
            self._validate_value(value)

        self._values = MappingProxyType(source)

    @staticmethod
    def _validate_name(name: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Persistent system field name is required.")

    @staticmethod
    def _validate_value(value: PersistentSystemFieldValue) -> None:
        if value is None:
            return

        if isinstance(value, Identifier):
            return

        validate_durable_value(value)

    @classmethod
    def empty(cls) -> PersistentSystemFieldState:
        return cls()

    def __getitem__(self, name: str) -> PersistentSystemFieldValue:
        return self._values[name]

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def keys(self) -> KeysView[str]:
        return self._values.keys()

    def values(self) -> ValuesView[PersistentSystemFieldValue]:
        return self._values.values()

    def items(self) -> ItemsView[str, PersistentSystemFieldValue]:
        return self._values.items()
