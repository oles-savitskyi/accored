from __future__ import annotations

from collections.abc import ItemsView, Iterator, KeysView, Mapping, ValuesView
from types import MappingProxyType
from typing import Self

from accore.platform.foundation import Identifier
from accore.platform.value.durable import (
    DurableValue,
    DurableValueError,
    validate_durable_value,
)

type SystemFieldIdentity = str
type DurableSystemFieldValue = DurableValue | Identifier
type NullableDurableSystemFieldValue = DurableSystemFieldValue | None


class DurableSystemFieldState:
    """Immutable runtime representation of durable system-field state.
    The container represents:
        SystemFieldIdentity -> DurableSystemFieldValue | None
    where:
    * a missing key represents MISSING;
    * ``None`` represents explicit NULL;
    * ``DurableValue`` represents a durable scalar or composite value;
    * ``Identifier`` represents a durable object identity value.
    The container does not define which system fields exist, whether they
    are applicable, required, nullable, or what semantic meaning a value has.
    Those concerns belong to Metadata and Validation.
    Object identity itself is not represented here. It remains structural
    identity owned by the object model.
    """

    __slots__ = ("_values",)

    def __init__(
        self,
        values: Mapping[
            SystemFieldIdentity,
            NullableDurableSystemFieldValue,
        ],
    ) -> None:
        snapshot: dict[
            SystemFieldIdentity,
            NullableDurableSystemFieldValue,
        ] = {}

        for identity, value in values.items():
            self._validate_system_field_identity(identity)
            snapshot[identity] = self._validate_system_field_value(
                identity,
                value,
            )

        self._values: Mapping[
            SystemFieldIdentity,
            NullableDurableSystemFieldValue,
        ] = MappingProxyType(snapshot)

    @classmethod
    def empty(cls) -> Self:
        """Create an empty durable system-field state."""
        return cls({})

    @staticmethod
    def _validate_system_field_identity(identity: object) -> None:
        if type(identity) is not str:
            raise DurableValueError(
                "System field identity must be a string, " f"got {type(identity).__name__}"
            )

        if not identity.strip():
            raise DurableValueError("System field identity must not be empty or whitespace-only")

    @staticmethod
    def _validate_system_field_value(
        identity: str,
        value: NullableDurableSystemFieldValue,
    ) -> NullableDurableSystemFieldValue:
        if value is None:
            return None

        if isinstance(value, Identifier):
            return value

        try:
            validate_durable_value(value)
        except DurableValueError as error:
            raise DurableValueError(
                f"System field {identity!r} contains an invalid durable value"
            ) from error

        return value

    def __getitem__(
        self,
        identity: SystemFieldIdentity,
    ) -> NullableDurableSystemFieldValue:
        return self._values[identity]

    def get(
        self,
        identity: SystemFieldIdentity,
        default: NullableDurableSystemFieldValue = None,
    ) -> NullableDurableSystemFieldValue:
        return self._values.get(identity, default)

    def __contains__(self, key: object) -> bool:
        return key in self._values

    def __iter__(self) -> Iterator[SystemFieldIdentity]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def keys(self) -> KeysView[SystemFieldIdentity]:
        return self._values.keys()

    def values(self) -> ValuesView[NullableDurableSystemFieldValue]:
        return self._values.values()

    def items(
        self,
    ) -> ItemsView[
        SystemFieldIdentity,
        NullableDurableSystemFieldValue,
    ]:
        return self._values.items()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DurableSystemFieldState):
            return NotImplemented

        return self._values == other._values

    def __repr__(self) -> str:
        return f"DurableSystemFieldState({dict(self._values)!r})"
