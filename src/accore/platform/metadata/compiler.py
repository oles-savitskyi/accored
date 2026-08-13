from __future__ import annotations

from accore.platform.definitions import CatalogDefinition, Definition
from accore.platform.metadata.catalog import CatalogMetadata


class MetadataCompiler:
    """Compile configuration definitions into runtime-independent metadata."""

    def compile(self, definition: Definition) -> CatalogMetadata:
        """Compile a supported definition into metadata."""
        if isinstance(definition, CatalogDefinition):
            identifier = definition.require_identifier()

            return CatalogMetadata(
                identifier=identifier,
                name=definition.name,
                source_definition_id=identifier,
            )

        raise TypeError(f"Unsupported definition type: {type(definition).__name__}")
