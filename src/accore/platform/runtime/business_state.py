from __future__ import annotations

from collections.abc import ItemsView, Iterator, KeysView, Mapping, ValuesView
from types import MappingProxyType
from typing import Self

from accore.platform.foundation.identity import Identifier

type BusinessStateDefinitionIdentity = Identifier
type StateValueIdentity = Identifier


class BusinessStateSnapshot:
    """Immutable snapshot of current durable business-state values.

    The snapshot represents:

        BusinessStateDefinitionIdentity -> StateValueIdentity

    It stores only the current state value for each business-state
    definition. Vocabulary membership, completeness, applicability, and
    transition legality are validated outside this container.
    """

    __slots__ = ("_values",)

    def __init__(
        self,
        values: Mapping[
            BusinessStateDefinitionIdentity,
            StateValueIdentity,
        ],
    ) -> None:
        snapshot = dict(values)

        for definition_identity, state_identity in snapshot.items():
            self._validate_identity(
                definition_identity,
                "business state definition identity",
            )
            self._validate_identity(
                state_identity,
                "state value identity",
            )

        self._values: Mapping[
            BusinessStateDefinitionIdentity,
            StateValueIdentity,
        ] = MappingProxyType(snapshot)

    @classmethod
    def empty(cls) -> Self:
        """Create an empty business-state snapshot."""
        return cls({})

    def __getitem__(
        self,
        definition_identity: BusinessStateDefinitionIdentity,
    ) -> StateValueIdentity:
        return self._values[definition_identity]

    def get(
        self,
        definition_identity: BusinessStateDefinitionIdentity,
        default: StateValueIdentity | None = None,
    ) -> StateValueIdentity | None:
        return self._values.get(definition_identity, default)

    def __contains__(self, key: object) -> bool:
        return key in self._values

    def __iter__(self) -> Iterator[BusinessStateDefinitionIdentity]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def keys(self) -> KeysView[BusinessStateDefinitionIdentity]:
        return self._values.keys()

    def values(self) -> ValuesView[StateValueIdentity]:
        return self._values.values()

    def items(
        self,
    ) -> ItemsView[
        BusinessStateDefinitionIdentity,
        StateValueIdentity,
    ]:
        return self._values.items()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BusinessStateSnapshot):
            return NotImplemented
        return self._values == other._values

    def __repr__(self) -> str:
        return f"BusinessStateSnapshot({dict(self._values)!r})"

    @staticmethod
    def _validate_identity(value: object, name: str) -> None:
        if not isinstance(value, Identifier):
            raise TypeError(f"{name} must be an Identifier, " f"got {type(value).__name__}")
