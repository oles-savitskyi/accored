from __future__ import annotations

from accore.platform.foundation import Identifier
from accore.platform.metadata.base import Metadata
from accore.platform.metadata.registry import MetadataRegistry


class RuntimeResolver:
    """Resolve runtime metadata through the metadata registry."""

    def __init__(self, registry: MetadataRegistry) -> None:
        self._registry = registry

    def resolve(self, identifier: Identifier) -> Metadata:
        """Resolve metadata by its identifier."""
        return self._registry.get(identifier)
