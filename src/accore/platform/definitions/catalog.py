from __future__ import annotations

from dataclasses import dataclass

from accore.platform.definitions.base import Definition, DefinitionType
from accore.platform.foundation import Identifier


@dataclass(frozen=True, slots=True)
class CatalogDefinition(Definition):
    """Declarative definition of a catalog."""

    def __init__(self, identifier: Identifier | None, name: str) -> None:
        super().__init__(
            identifier=identifier,
            name=name,
            definition_type=DefinitionType.CATALOG,
        )
