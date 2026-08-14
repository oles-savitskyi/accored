from accore.platform.foundation import Identifier
from accore.platform.metadata.catalog import CatalogMetadata
from accore.platform.metadata.registry import MetadataRegistry
from accore.platform.runtime.catalog import CatalogRuntime


class RuntimeResolver:
    def __init__(self, registry: MetadataRegistry) -> None:
        self._registry = registry

    def resolve(self, identifier: Identifier) -> CatalogRuntime:
        metadata = self._registry.get(identifier)

        if not isinstance(metadata, CatalogMetadata):
            raise TypeError(f"Unsupported metadata type: {type(metadata).__name__}")

        return CatalogRuntime(metadata)
