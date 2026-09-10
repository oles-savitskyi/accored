from __future__ import annotations

from typing import Any, Protocol

from accore.platform.configuration.identity import ConfigurationIdentity

# PersistentConfiguration is an architectural persistence representation. Its
# concrete shape is intentionally deferred until configuration persistence
# representation is defined.
PersistentConfiguration = Any


class ConfigurationPersistence(Protocol):
    """Persistence contract for durable configuration state."""

    def create(self, configuration: PersistentConfiguration) -> None:
        """Create a persistent configuration under its logical identity."""

    def get(self, identity: ConfigurationIdentity) -> PersistentConfiguration:
        """Retrieve a persistent configuration by logical identity."""

    def update(self, configuration: PersistentConfiguration) -> None:
        """Update an existing persistent configuration."""
