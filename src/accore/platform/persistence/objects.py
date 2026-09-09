from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from accore.platform.foundation.identity import Identifier
from accore.platform.persistence.business_state import PersistentBusinessState
from accore.platform.persistence.field_state import PersistentFieldState
from accore.platform.persistence.reference_state import PersistentReferenceState
from accore.platform.persistence.system_field_state import (
    PersistentSystemFieldState,
)


@dataclass(frozen=True, slots=True)
class PersistentObjectState:
    """Immutable durable state of a persistent object."""

    fields: PersistentFieldState
    references: PersistentReferenceState
    business_state: PersistentBusinessState
    system_fields: PersistentSystemFieldState


@dataclass(frozen=True, slots=True)
class PersistentObject:
    """Immutable durable representation of a business object."""

    identity: Identifier
    object_type_identity: Identifier
    state: PersistentObjectState


class ObjectPersistence(Protocol):
    def create(self, obj: PersistentObject) -> None: ...

    def get(self, identity: Identifier) -> PersistentObject: ...

    def update(self, obj: PersistentObject) -> None: ...


class ObjectDeletion(Protocol):
    def delete(self, identity: Identifier) -> None: ...
