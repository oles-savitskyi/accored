from __future__ import annotations

from accore.platform.configuration.runtime_binding import (
    RuntimeConfigurationBinding,
    RuntimeConfigurationBindingError,
)
from accore.platform.foundation.identity import Identifier
from accore.platform.metadata.base import Metadata


class RuntimeConfigurationError(RuntimeError):
    """Raised when no active runtime configuration is available."""


class MetadataResolutionError(LookupError):
    """Raised when metadata cannot be resolved from the active configuration."""

    def __init__(self, identifier: Identifier) -> None:
        self.identifier = identifier
        super().__init__(
            f"Metadata with identifier {identifier!s} is not present "
            "in the active configuration."
        )


class MetadataResolver:
    """Resolve metadata from the currently bound runtime configuration."""

    def __init__(self, binding: RuntimeConfigurationBinding) -> None:
        self._binding = binding

    def resolve(self, identifier: Identifier) -> Metadata:
        """Resolve metadata by logical identifier.

        Raises:
            RuntimeConfigurationError: If no active configuration is bound.
            MetadataResolutionError: If the metadata is not present in the
                active configuration.
        """
        try:
            configuration = self._binding.get()
        except RuntimeConfigurationBindingError as exc:
            raise RuntimeConfigurationError("No active runtime configuration is bound.") from exc

        try:
            return configuration.metadata_registry.get(identifier)
        except KeyError as exc:
            raise MetadataResolutionError(identifier) from exc
