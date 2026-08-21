from __future__ import annotations

from accore.platform.configuration.context import RuntimeConfigurationContext
from accore.platform.foundation.identity import Identifier
from accore.platform.metadata.base import Metadata


class MetadataResolutionError(LookupError):
    """Raised when metadata cannot be resolved from the runtime context."""

    def __init__(self, identifier: Identifier) -> None:
        self.identifier = identifier
        super().__init__(
            f"Metadata with identifier {identifier!s} is not present "
            "in the runtime configuration context."
        )


class MetadataResolver:
    """Resolve metadata within an explicit runtime configuration context."""

    def resolve(
        self,
        context: RuntimeConfigurationContext,
        identifier: Identifier,
    ) -> Metadata:
        """Resolve metadata by logical identifier within a runtime context.

        Raises:
            MetadataResolutionError: If the metadata is not present in the
                supplied runtime configuration context.
        """
        try:
            return context.configuration.metadata_registry.get(identifier)
        except KeyError as exc:
            raise MetadataResolutionError(identifier) from exc
