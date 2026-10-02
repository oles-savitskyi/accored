from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from accore.platform.foundation.identity import Identifier


class SessionState(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"


@dataclass(frozen=True, slots=True)
class Session:
    """Runtime authentication session artifact."""

    identity: Identifier
    principal_identity: Identifier
    created_at: datetime
    expires_at: datetime
    state: SessionState
