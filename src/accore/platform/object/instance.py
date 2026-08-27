from __future__ import annotations

from dataclasses import dataclass

from accore.platform.foundation.identity import Identifier


@dataclass(eq=False, slots=True)
class ObjectInstance:
    """Runtime representation of an individual object instance."""

    identity: Identifier

    def __eq__(self, other: object) -> bool:
        """Compare object instances by identity."""
        if not isinstance(other, ObjectInstance):
            return NotImplemented

        return self.identity == other.identity
