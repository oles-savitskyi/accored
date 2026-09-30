from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from accore.platform.foundation import Identifier

from .errors import ValuationValidationError
from .plan import ConsumptionPlan, LayerEstablishmentPlan, ValuationPlanOperation


@dataclass(frozen=True, slots=True)
class ValuationOperationIdentity:
    """Immutable identity of one logical valuation lifecycle operation."""

    value: str


class ValuationOperationType(StrEnum):
    """Logical valuation lifecycle operation types."""

    ESTABLISH = "establish"
    REMOVE = "remove"


@dataclass(frozen=True, slots=True)
class ValuationEstablishRecoveryDescriptor:
    """Immutable semantic payload sufficient to reconstruct an ESTABLISH plan."""

    document_identity: Identifier
    operations: tuple[ValuationPlanOperation, ...]

    def __post_init__(self) -> None:
        if not self.operations:
            raise ValuationValidationError(
                "ESTABLISH recovery descriptor must contain at least one operation."
            )

        for operation in self.operations:
            if isinstance(operation, LayerEstablishmentPlan):
                operation_document_identity = operation.source_document_identity
            elif isinstance(operation, ConsumptionPlan):
                operation_document_identity = operation.document_identity
            else:
                raise ValuationValidationError("Unsupported valuation plan operation.")
            if operation_document_identity != self.document_identity:
                raise ValuationValidationError(
                    "All ESTABLISH recovery operations must belong to the descriptor document."
                )


@dataclass(frozen=True, slots=True)
class ValuationOperationRecord:
    """Immutable authoritative record of one valuation lifecycle operation."""

    identity: ValuationOperationIdentity
    operation_type: ValuationOperationType
    document_identity: Identifier
    fingerprint: str
    target_fact_identities: tuple[Identifier, ...] = ()
    establish_descriptor: ValuationEstablishRecoveryDescriptor | None = None

    def __post_init__(self) -> None:
        if self.operation_type is ValuationOperationType.ESTABLISH:
            if self.target_fact_identities:
                raise ValuationValidationError(
                    "ESTABLISH operation must not contain REMOVE target fact identities."
                )
            if self.establish_descriptor is not None and (
                self.establish_descriptor.document_identity != self.document_identity
            ):
                raise ValuationValidationError(
                    "ESTABLISH recovery descriptor document identity must match the operation."
                )
            return

        if self.operation_type is ValuationOperationType.REMOVE:
            if self.establish_descriptor is not None:
                raise ValuationValidationError(
                    "REMOVE operation must not contain an ESTABLISH recovery descriptor."
                )
            return

        raise ValuationValidationError("Unsupported valuation operation type.")
