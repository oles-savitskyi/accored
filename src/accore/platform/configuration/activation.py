from __future__ import annotations

from dataclasses import dataclass

from accore.platform.configuration.candidate import ConfigurationCandidate
from accore.platform.configuration.identity import (
    ConfigurationIdentity,
    ConfigurationVersion,
)
from accore.platform.configuration.lifecycle import ConfigurationLifecycleState
from accore.platform.metadata.registry import MetadataRegistry


@dataclass(frozen=True, slots=True)
class ActiveConfiguration:
    """Immutable runtime-visible configuration snapshot."""

    identity: ConfigurationIdentity
    version: ConfigurationVersion
    metadata_registry: MetadataRegistry


class ConfigurationActivator:
    """Publish validated configuration candidates as the active configuration."""

    def __init__(self) -> None:
        self._current: ActiveConfiguration | None = None

    def activate(self, candidate: ConfigurationCandidate) -> ActiveConfiguration:
        """Activate a validated configuration candidate.

        Raises:
            ValueError: If the candidate is not in VALIDATED state.
        """
        if candidate.state is not ConfigurationLifecycleState.VALIDATED:
            raise ValueError("Only VALIDATED configuration candidates can be activated.")

        active = ActiveConfiguration(
            identity=candidate.identity,
            version=candidate.version,
            metadata_registry=candidate.metadata_registry,
        )

        self._current = active
        return active

    def current(self) -> ActiveConfiguration | None:
        """Return the currently active configuration, if any."""
        return self._current
