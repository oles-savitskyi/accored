from __future__ import annotations

from dataclasses import dataclass

from accore.platform.foundation import Identifier
from accore.platform.runtime import CatalogRuntime

from .context import ObjectContext
from .state import ObjectState


@dataclass(frozen=True, eq=False)
class ObjectInstance:
    """Immutable runtime representation of one business object."""

    identity: Identifier
    object_type: CatalogRuntime
    context: ObjectContext
    state: ObjectState = ObjectState.CREATED

    def __post_init__(self) -> None:
        if self.state is not ObjectState.CREATED:
            raise ValueError("ObjectInstance must be created in CREATED state.")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ObjectInstance):
            return NotImplemented

        return self.identity == other.identity

    def __hash__(self) -> int:
        return hash(self.identity)
