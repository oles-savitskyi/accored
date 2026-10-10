from __future__ import annotations

from dataclasses import dataclass

from accore.platform.foundation.identity import Identifier
from accore.platform.security.context import SecurityContext

from .contract import IntegrationContractIdentity


@dataclass(frozen=True, slots=True)
class CommandRequest[P]:
    """Request to perform a state-changing Integration operation."""

    contract: IntegrationContractIdentity
    payload: P
    security_context: SecurityContext
    request_identity: Identifier


@dataclass(frozen=True, slots=True)
class QueryRequest[P]:
    """Request to retrieve information through an Integration operation."""

    contract: IntegrationContractIdentity
    payload: P
    security_context: SecurityContext
    request_identity: Identifier
