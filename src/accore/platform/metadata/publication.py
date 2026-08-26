from __future__ import annotations

from accore.platform.foundation import Identifier
from accore.platform.metadata.base import Metadata


class PublishedMetadataView:
    """Immutable read-only view of published metadata."""

    def __init__(self, metadata: tuple[Metadata, ...]) -> None:
        self._metadata = {item.identifier: item for item in metadata}

    def get(self, identifier: Identifier) -> Metadata:
        """Return published metadata by identity."""
        try:
            return self._metadata[identifier]
        except KeyError:
            raise KeyError(f"Metadata not found: {identifier}") from None

    def contains(self, identifier: Identifier) -> bool:
        """Return whether published metadata exists."""
        return identifier in self._metadata

    def all(self) -> tuple[Metadata, ...]:
        """Return all published metadata."""
        return tuple(self._metadata.values())
