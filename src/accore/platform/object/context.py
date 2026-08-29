from __future__ import annotations

from dataclasses import dataclass

from accore.platform.configuration import RuntimeConfigurationContext


@dataclass(frozen=True)
class ObjectContext:
    runtime_context: RuntimeConfigurationContext
