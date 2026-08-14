from dataclasses import dataclass

from accore.platform.metadata.catalog import CatalogMetadata


@dataclass(frozen=True, slots=True)
class CatalogRuntime:
    metadata: CatalogMetadata
