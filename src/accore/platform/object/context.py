from __future__ import annotations

from dataclasses import dataclass

from accore.platform.configuration import RuntimeConfigurationContext


@dataclass(frozen=True, slots=True)
class ObjectContext:
    """Immutable execution context of an object instance."""

    runtime_configuration_context: RuntimeConfigurationContext
