from __future__ import annotations

from dataclasses import dataclass

from accore.platform.configuration.candidate import ConfigurationCandidate
from accore.platform.configuration.identity import (
    ConfigurationIdentity,
    ConfigurationVersion,
)
from accore.platform.configuration.lifecycle import ConfigurationLifecycleState
from accore.platform.metadata.publication import PublishedMetadataView


@dataclass(frozen=True, slots=True)
class ActiveConfiguration:
    """Immutable runtime-visible configuration snapshot."""

    identity: ConfigurationIdentity
    version: ConfigurationVersion
    published_metadata: PublishedMetadataView


class ConfigurationActivator:
    """Create active configurations from validated configuration candidates."""

    def activate(self, candidate: ConfigurationCandidate) -> ActiveConfiguration:
        """Activate a validated configuration candidate.

        Raises:
            ValueError: If the candidate is not in VALIDATED state.
        """
        if candidate.state is not ConfigurationLifecycleState.VALIDATED:
            raise ValueError("Only VALIDATED configuration candidates can be activated.")

        published_metadata = candidate.metadata_registry.publish()

        return ActiveConfiguration(
            identity=candidate.identity,
            version=candidate.version,
            published_metadata=published_metadata,
        )
