from __future__ import annotations

from accore.platform.configuration.activation import ActiveConfiguration
from accore.platform.configuration.context import RuntimeConfigurationContext


class RuntimeConfigurationBindingError(RuntimeError):
    """Raised when runtime configuration has not been bound."""


class RuntimeConfigurationBinding:
    """Explicit binding to the currently active configuration."""

    def __init__(self) -> None:
        self._active_configuration: ActiveConfiguration | None = None

    def bind(self, configuration: ActiveConfiguration) -> None:
        """Bind the supplied active configuration."""
        self._active_configuration = configuration

    def get(self) -> ActiveConfiguration:
        """Return the currently bound active configuration.

        Raises:
            RuntimeConfigurationBindingError:
                If no configuration is currently bound.
        """
        if self._active_configuration is None:
            raise RuntimeConfigurationBindingError("Runtime configuration is not bound.")

        return self._active_configuration

    def acquire(self) -> RuntimeConfigurationContext:
        """Capture the currently bound configuration as a runtime context.

        Raises:
            RuntimeConfigurationBindingError:
                If no configuration is currently bound.
        """
        return RuntimeConfigurationContext(configuration=self.get())
