from __future__ import annotations

from accore.platform.definitions import AttributeDefinition, CatalogDefinition, Definition
from accore.platform.metadata.attribute import AttributeMetadata
from accore.platform.metadata.catalog import CatalogMetadata
from accore.platform.metadata.system_fields import default_catalog_system_fields


class MetadataCompiler:
    """Compile configuration definitions into runtime-independent metadata."""

    def compile(self, definition: Definition) -> CatalogMetadata:
        """Compile a supported definition into metadata."""
        if isinstance(definition, CatalogDefinition):
            identifier = definition.require_identifier()

            definition.validate()

            attributes = tuple(
                self._compile_attribute(attribute) for attribute in definition.attributes
            )

            return CatalogMetadata(
                identifier=identifier,
                name=definition.name,
                source_definition_id=identifier,
                system_fields=default_catalog_system_fields(),
                attributes=attributes,
            )

        raise TypeError(f"Unsupported definition type: {type(definition).__name__}")

    @staticmethod
    def _compile_attribute(
        definition: AttributeDefinition,
    ) -> AttributeMetadata:
        definition.validate()

        return AttributeMetadata(
            name=definition.name,
            attribute_type=definition.attribute_type,
            nullable=definition.nullable,
            default_value=definition.default_value,
            description=definition.description,
            reference_target=definition.reference_target,
        )
