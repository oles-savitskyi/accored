from __future__ import annotations

from dataclasses import dataclass, field

from accore.platform.configuration.identity import (
    ConfigurationIdentity,
    ConfigurationVersion,
)
from accore.platform.configuration.lifecycle import ConfigurationLifecycleState
from accore.platform.metadata.registry import MetadataRegistry


@dataclass(slots=True)
class ConfigurationCandidate:
    """Isolated metadata configuration candidate."""

    identity: ConfigurationIdentity
    version: ConfigurationVersion
    metadata_registry: MetadataRegistry
    state: ConfigurationLifecycleState = field(
        default=ConfigurationLifecycleState.LOADED,
        init=False,
    )

    def mark_validated(self) -> None:
        """Mark the candidate as validated."""
        if self.state is not ConfigurationLifecycleState.LOADED:
            raise ValueError(
                f"Candidate cannot transition to VALIDATED from " f"{self.state.value!r}."
            )

        self.state = ConfigurationLifecycleState.VALIDATED
