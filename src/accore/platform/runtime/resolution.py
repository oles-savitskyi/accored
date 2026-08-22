from __future__ import annotations

from accore.platform.configuration.context import RuntimeConfigurationContext
from accore.platform.configuration.resolver import MetadataResolver
from accore.platform.foundation import Identifier
from accore.platform.metadata.catalog import CatalogMetadata
from accore.platform.runtime.catalog import CatalogRuntime


class RuntimeResolver:
    """Resolve runtime objects within an explicit runtime configuration context."""

    def __init__(self, metadata_resolver: MetadataResolver) -> None:
        self._metadata_resolver = metadata_resolver

    def resolve(
        self,
        context: RuntimeConfigurationContext,
        identifier: Identifier,
    ) -> CatalogRuntime:
        """Resolve a runtime object by logical identifier.

        The runtime object is created from metadata resolved within the
        supplied runtime configuration context.
        """
        metadata = self._metadata_resolver.resolve(context, identifier)

        if not isinstance(metadata, CatalogMetadata):
            raise TypeError(f"Unsupported metadata type: {type(metadata).__name__}")

        return CatalogRuntime(metadata)
