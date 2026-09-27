from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from accore.platform.foundation import Identifier

from .errors import ValuationValidationError
from .key import ValuationKey


@dataclass(frozen=True, slots=True)
class ValuationLayer:
    """Immutable valuation layer representing quantity available for consumption."""

    identity: Identifier
    valuation_key: ValuationKey
    quantity: Decimal
    total_cost: Decimal
    source_document_identity: Identifier
    source_movement_identity: Identifier
    created_at: datetime

    def __post_init__(self) -> None:
        if self.quantity <= Decimal(0):
            raise ValuationValidationError("ValuationLayer quantity must be greater than zero.")

        if self.total_cost < Decimal(0):
            raise ValuationValidationError("ValuationLayer total_cost cannot be negative.")


@dataclass(frozen=True, slots=True)
class ValuationConsumption:
    """Immutable valuation consumption from a specific valuation layer."""

    identity: Identifier
    valuation_key: ValuationKey
    layer_identity: Identifier
    quantity: Decimal
    cost: Decimal
    document_identity: Identifier
    source_identity: Identifier
    created_at: datetime

    def __post_init__(self) -> None:
        if self.quantity <= Decimal(0):
            raise ValuationValidationError(
                "ValuationConsumption quantity must be greater than zero."
            )

        if self.cost < Decimal(0):
            raise ValuationValidationError("ValuationConsumption cost cannot be negative.")


@dataclass(frozen=True, slots=True)
class ValuationAdjustment:
    """Immutable additional valuation amount."""

    identity: Identifier
    valuation_key: ValuationKey
    amount: Decimal
    source_identity: Identifier
    reason: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ValuationAllocation:
    """Immutable allocation of an adjustment to a valuation layer."""

    identity: Identifier
    adjustment_identity: Identifier
    layer_identity: Identifier
    valuation_key: ValuationKey
    amount: Decimal
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ValuationReversal:
    """Immutable compensating fact reversing another valuation fact."""

    identity: Identifier
    reversed_identity: Identifier
    valuation_key: ValuationKey
    document_identity: Identifier
    source_identity: Identifier
    created_at: datetime


type ValuationFact = (
    ValuationLayer
    | ValuationConsumption
    | ValuationAdjustment
    | ValuationAllocation
    | ValuationReversal
)
