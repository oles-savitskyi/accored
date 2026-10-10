from __future__ import annotations

from dataclasses import dataclass

from accore.platform.foundation.identity import Identifier


@dataclass(frozen=True, slots=True)
class CommandResponse[R]:
    """Result of an Integration command, correlated to its request."""

    request_identity: Identifier
    result: R


@dataclass(frozen=True, slots=True)
class QueryResponse[R]:
    """Result of an Integration query, correlated to its request."""

    request_identity: Identifier
    result: R
