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


class PersistentBusinessState(Mapping[Identifier, Identifier]):
    """Immutable persistence-side snapshot of current business states."""

    def __init__(
        self,
        values: Mapping[Identifier, Identifier] | None = None,
    ) -> None:
        source = {} if values is None else dict(values)

        for definition_identity, state_identity in source.items():
            self._validate_identity(
                definition_identity,
                "Business state definition identity",
            )
            self._validate_identity(
                state_identity,
                "Business state value identity",
            )

        self._values = MappingProxyType(source)

    @staticmethod
    def _validate_identity(
        value: Identifier,
        label: str,
    ) -> None:
        if not isinstance(value, Identifier):
            raise TypeError(f"{label} must be an Identifier.")

    @classmethod
    def empty(cls) -> PersistentBusinessState:
        return cls()

    def __getitem__(self, identity: Identifier) -> Identifier:
        return self._values[identity]

    def __iter__(self) -> Iterator[Identifier]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def keys(self) -> KeysView[Identifier]:
        return self._values.keys()

    def values(self) -> ValuesView[Identifier]:
        return self._values.values()

    def items(self) -> ItemsView[Identifier, Identifier]:
        return self._values.items()
