from __future__ import annotations

from accore.platform.foundation import Identifier
from accore.platform.metadata.base import Metadata


class MetadataRegistry:
    """In-memory registry of compiled metadata."""

    def __init__(self) -> None:
        self._metadata: dict[Identifier, Metadata] = {}

    def register(self, metadata: Metadata) -> None:
        """Register metadata under its identity."""
        if metadata.identifier in self._metadata:
            raise KeyError(f"Metadata already registered: {metadata.identifier}")

        self._metadata[metadata.identifier] = metadata

    def get(self, identifier: Identifier) -> Metadata:
        """Return registered metadata by identity."""
        try:
            return self._metadata[identifier]
        except KeyError:
            raise KeyError(f"Metadata not found: {identifier}") from None

    def contains(self, identifier: Identifier) -> bool:
        """Return whether metadata is registered."""
        return identifier in self._metadata

    def all(self) -> tuple[Metadata, ...]:
        """Return all registered metadata."""
        return tuple(self._metadata.values())
