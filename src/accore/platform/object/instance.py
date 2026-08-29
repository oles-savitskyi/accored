from __future__ import annotations

from dataclasses import dataclass, field

from accore.platform.foundation import Identifier
from accore.platform.object.context import ObjectContext
from accore.platform.object.state import ObjectState
from accore.platform.runtime.catalog import CatalogRuntime


@dataclass(eq=False, slots=True)
class ObjectInstance:
    """Runtime instance of a concrete object type."""

    identity: Identifier
    object_type: CatalogRuntime
    context: ObjectContext
    state: ObjectState = field(
        default=ObjectState.CREATED,
        init=False,
    )

    def __eq__(self, other: object) -> bool:
        """Compare object instances by identity."""
        if not isinstance(other, ObjectInstance):
            return NotImplemented

        return self.identity == other.identity

    def __hash__(self) -> int:
        """Return a hash based on object identity."""
        return hash(self.identity)
