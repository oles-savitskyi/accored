from __future__ import annotations

from dataclasses import dataclass

from accore.platform.definitions.attribute import AttributeDefinition
from accore.platform.definitions.base import Definition, DefinitionType
from accore.platform.foundation import DefinitionError, Identifier


@dataclass(frozen=True, slots=True)
class CatalogDefinition(Definition):
    """Declarative definition of a catalog."""

    attributes: tuple[AttributeDefinition, ...]

    def __init__(
        self,
        identifier: Identifier | None,
        name: str,
        attributes: tuple[AttributeDefinition, ...] = (),
    ) -> None:
        super().__init__(
            identifier=identifier,
            name=name,
            definition_type=DefinitionType.CATALOG,
        )
        object.__setattr__(self, "attributes", attributes)

    def validate(self) -> None:
        """Validate the catalog definition."""
        super().validate()

        names: set[str] = set()

        for attribute in self.attributes:
            attribute.validate()

            if attribute.name in names:
                raise DefinitionError(f"Duplicate attribute name: '{attribute.name}'.")

            names.add(attribute.name)
