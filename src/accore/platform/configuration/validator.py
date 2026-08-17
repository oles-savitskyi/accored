from __future__ import annotations

from accore.platform.configuration.candidate import ConfigurationCandidate
from accore.platform.configuration.lifecycle import ConfigurationLifecycleState
from accore.platform.foundation import MetadataError


class ConfigurationValidationError(MetadataError):
    """Raised when a configuration candidate is not valid."""


class ConfigurationValidator:
    """Validate a loaded configuration candidate."""

    def validate(self, candidate: ConfigurationCandidate) -> None:
        """Validate the candidate and transition it to VALIDATED."""
        if candidate.state is ConfigurationLifecycleState.VALIDATED:
            return

        if candidate.state is not ConfigurationLifecycleState.LOADED:
            raise ConfigurationValidationError(
                f"Configuration candidate cannot be validated from state "
                f"{candidate.state.value!r}."
            )

        self._validate_metadata(candidate)
        candidate.mark_validated()

        candidate.state = ConfigurationLifecycleState.VALIDATED

    @staticmethod
    def _validate_metadata(candidate: ConfigurationCandidate) -> None:
        """Validate metadata contained in the candidate."""
        for metadata in candidate.metadata_registry.all():
            if not metadata.name.strip():
                raise ConfigurationValidationError("Configuration metadata name must not be empty.")
