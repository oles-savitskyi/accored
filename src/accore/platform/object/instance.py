from __future__ import annotations

from dataclasses import dataclass

from accore.platform.foundation.identity import Identifier
from accore.platform.runtime.catalog import CatalogRuntime


@dataclass(eq=False, slots=True)
class ObjectInstance:
    """Runtime representation of an individual object instance."""

    identity: Identifier
    object_type: CatalogRuntime

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ObjectInstance):
            return NotImplemented

        return self.identity == other.identity
