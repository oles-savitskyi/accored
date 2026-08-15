from __future__ import annotations

from accore.platform.definitions import CatalogDefinition, Definition
from accore.platform.validation.attributes import validate_attribute_semantics


class DefinitionValidator:
    """Validate configuration definitions before compilation."""

    def validate(self, definition: Definition) -> None:
        """Validate a supported definition."""

        if isinstance(definition, CatalogDefinition):
            definition.validate()

            for attribute in definition.attributes:
                validate_attribute_semantics(attribute)

            return

        raise TypeError(f"Unsupported definition type: {type(definition).__name__}")
