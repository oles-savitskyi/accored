from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from accore.platform.foundation import Identifier


@dataclass(frozen=True, slots=True)
class ValuationOperationIdentity:
    """Immutable identity of one logical valuation lifecycle operation."""

    value: str


class ValuationOperationType(StrEnum):
    """Logical valuation lifecycle operation types."""

    ESTABLISH = "establish"
    REMOVE = "remove"


@dataclass(frozen=True, slots=True)
class ValuationOperationRecord:
    """Immutable authoritative record of one valuation lifecycle operation."""

    identity: ValuationOperationIdentity
    operation_type: ValuationOperationType
    document_identity: Identifier
    fingerprint: str
    target_fact_identities: tuple[Identifier, ...] = ()
