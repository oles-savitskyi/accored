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
    """Create active configurations from validated configuration candidates."""

    def activate(self, candidate: ConfigurationCandidate) -> ActiveConfiguration:
        """Activate a validated configuration candidate.

        Raises:
            ValueError: If the candidate is not in VALIDATED state.
        """
        if candidate.state is not ConfigurationLifecycleState.VALIDATED:
            raise ValueError("Only VALIDATED configuration candidates can be activated.")

        return ActiveConfiguration(
            identity=candidate.identity,
            version=candidate.version,
            metadata_registry=candidate.metadata_registry,
        )
