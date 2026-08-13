from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from accore.platform.foundation import DefinitionError, Identifier


class DefinitionType(str, Enum):
    """Supported configuration definition types."""

    CATALOG = "catalog"


@dataclass(frozen=True, slots=True)
class Definition:
    """Immutable declarative description of a configuration object."""

    identifier: Identifier | None
    name: str
    definition_type: DefinitionType

    def validate(self) -> None:
        """Validate the definition.

        Raises:
            DefinitionError: If the definition is invalid.
        """
        if self.identifier is None:
            raise DefinitionError("Definition identifier is required.")

        if not self.name.strip():
            raise DefinitionError("Definition name is required.")

    def require_identifier(self) -> Identifier:
        """Return the identifier after validation."""
        self.validate()

        if self.identifier is None:
            raise DefinitionError("Definition identifier is required.")

        return self.identifier
