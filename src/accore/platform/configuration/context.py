from __future__ import annotations

from dataclasses import dataclass

from accore.platform.configuration.activation import ActiveConfiguration
from accore.platform.configuration.identity import (
    ConfigurationIdentity,
    ConfigurationVersion,
)


@dataclass(frozen=True, slots=True)
class RuntimeConfigurationContext:
    """Immutable runtime configuration snapshot."""

    configuration: ActiveConfiguration

    @property
    def identity(self) -> ConfigurationIdentity:
        """Return the identity of the captured configuration."""
        return self.configuration.identity

    @property
    def version(self) -> ConfigurationVersion:
        """Return the version of the captured configuration."""
        return self.configuration.version
