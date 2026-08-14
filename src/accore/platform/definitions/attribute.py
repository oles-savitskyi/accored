from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from accore.platform.foundation import DefinitionError


class AttributeType(str, Enum):
    """Supported attribute data types."""

    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    REFERENCE = "reference"
    ENUM = "enum"


@dataclass(frozen=True, slots=True)
class AttributeDefinition:
    """Immutable declarative definition of a business attribute."""

    name: str
    attribute_type: AttributeType
    nullable: bool = True
    default_value: Any = None
    description: str = ""
    reference_target: str | None = None

    def validate(self) -> None:
        """Validate the attribute definition.

        Raises:
            DefinitionError: If the attribute definition is invalid.
        """
        if not self.name.strip():
            raise DefinitionError("Attribute name is required.")

        if self.attribute_type is AttributeType.REFERENCE:
            if self.reference_target is None:
                raise DefinitionError(f"Reference attribute '{self.name}' requires a target.")

            if not self.reference_target.strip():
                raise DefinitionError(f"Reference attribute '{self.name}' requires a target.")

        elif self.reference_target is not None:
            raise DefinitionError(f"Attribute '{self.name}' cannot define a reference target.")
