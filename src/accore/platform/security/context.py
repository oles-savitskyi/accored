from __future__ import annotations

from dataclasses import dataclass

from accore.platform.foundation.identity import Identifier

from .principal import Principal
from .session import Session


@dataclass(frozen=True, slots=True)
class SecurityContext:
    """Immutable security snapshot for one protected execution."""

    principal: Principal | None
    session: Session | None
    request_identity: Identifier | None = None
