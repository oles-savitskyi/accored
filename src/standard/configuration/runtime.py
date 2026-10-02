from __future__ import annotations

from dataclasses import dataclass

from accore.platform.foundation import Identifier


@dataclass(frozen=True, slots=True)
class StandardRuntimeConfiguration:
    """Immutable Standard-specific runtime configuration projection."""

    inventory_register_identity: Identifier
