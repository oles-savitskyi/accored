from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from accore.platform.foundation import Identifier

from .errors import ValuationValidationError
from .key import ValuationKey


@dataclass(frozen=True, slots=True)
class PlannedLayerReference:
    """Local reference to a layer established by the same valuation plan."""

    value: Identifier


@dataclass(frozen=True, slots=True)
class PersistedLayerReference:
    """Reference to an already persisted valuation layer."""

    identity: Identifier


type LayerReference = PlannedLayerReference | PersistedLayerReference


@dataclass(frozen=True, slots=True)
class LayerEstablishmentPlan:
    """Deterministic instruction for establishing one valuation layer."""

    reference: PlannedLayerReference
    valuation_key: ValuationKey
    quantity: Decimal
    source_document_identity: Identifier
    source_movement_identity: Identifier
    created_at: datetime

    def __post_init__(self) -> None:
        if self.quantity <= Decimal(0):
            raise ValuationValidationError(
                "LayerEstablishmentPlan quantity must be greater than zero."
            )


@dataclass(frozen=True, slots=True)
class ConsumptionPlan:
    """Deterministic instruction for establishing one valuation consumption fact."""

    valuation_key: ValuationKey
    layer_reference: LayerReference
    quantity: Decimal
    cost: Decimal
    source_identity: Identifier
    created_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.quantity, Decimal):
            raise TypeError("ConsumptionPlan quantity must be a Decimal.")
        if self.quantity <= Decimal(0):
            raise ValuationValidationError("ConsumptionPlan quantity must be greater than zero.")
        if not isinstance(self.cost, Decimal):
            raise TypeError("ConsumptionPlan cost must be a Decimal.")
        if self.cost < Decimal(0):
            raise ValuationValidationError("ConsumptionPlan cost cannot be negative.")


type ValuationPlanOperation = LayerEstablishmentPlan | ConsumptionPlan


@dataclass(frozen=True, slots=True)
class ValuationPlan:
    """Immutable deterministic valuation plan produced by valuation preflight."""

    operations: tuple[ValuationPlanOperation, ...]
