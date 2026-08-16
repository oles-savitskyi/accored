from __future__ import annotations

from dataclasses import dataclass

from accore.platform.foundation import Identifier
from accore.platform.metadata.attribute import AttributeMetadata
from accore.platform.metadata.catalog import CatalogMetadata
from accore.platform.metadata.system_field import SystemFieldMetadata
from accore.platform.runtime.errors import MetadataLookupError


@dataclass(frozen=True, slots=True)
class CatalogRuntime:
    """Runtime representation of a catalog backed exclusively by metadata."""

    metadata: CatalogMetadata

    def metadata_identity(self) -> Identifier:
        """Return the identity of the metadata represented by this runtime object."""
        return self.metadata.identifier

    def attributes(self) -> tuple[AttributeMetadata, ...]:
        """Return all catalog attribute metadata."""
        return self.metadata.attributes

    def attribute(self, name: str) -> AttributeMetadata:
        """Return metadata for a catalog attribute by name.

        Raises:
            MetadataLookupError: If the attribute does not exist.
        """
        for attribute in self.metadata.attributes:
            if attribute.name == name:
                return attribute

        raise MetadataLookupError(
            f"Attribute '{name}' does not exist in catalog '{self.metadata.name}'."
        )

    def system_fields(self) -> tuple[SystemFieldMetadata, ...]:
        """Return all platform-managed system field metadata."""
        return self.metadata.system_fields
