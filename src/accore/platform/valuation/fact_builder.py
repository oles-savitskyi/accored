from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from accore.platform.foundation import Identifier

from .errors import ValuationValidationError
from .fact_identity import DefaultValuationFactIdentityFactory
from .facts import (
    ValuationConsumption,
    ValuationFact,
    ValuationFactIdentityFactory,
    ValuationFactType,
    ValuationLayer,
)
from .operations import ValuationOperationIdentity
from .plan import (
    ConsumptionPlan,
    LayerEstablishmentPlan,
    PersistedLayerReference,
    PlannedLayerReference,
    ValuationPlan,
)


class ValuationFactBuilder(Protocol):
    """Build deterministic authoritative valuation facts from a valuation plan."""

    def build(
        self,
        plan: ValuationPlan,
        operation_identity: ValuationOperationIdentity,
    ) -> tuple[ValuationFact, ...]: ...


class DefaultValuationFactBuilder:
    """Construct immutable valuation facts without performing persistence."""

    def __init__(
        self,
        *,
        fact_identity_factory: ValuationFactIdentityFactory | None = None,
    ) -> None:
        self._fact_identity_factory = fact_identity_factory or DefaultValuationFactIdentityFactory()

    def build(
        self,
        plan: ValuationPlan,
        operation_identity: ValuationOperationIdentity,
    ) -> tuple[ValuationFact, ...]:
        references: dict[PlannedLayerReference, Identifier] = {}
        facts: list[ValuationFact] = []

        for operation in plan.operations:
            if isinstance(operation, LayerEstablishmentPlan):
                identity = self._fact_identity_factory.for_operation_fact(
                    operation_identity,
                    ValuationFactType.LAYER,
                    (
                        operation.valuation_key,
                        operation.quantity,
                        operation.source_document_identity,
                        operation.source_movement_identity,
                        operation.created_at,
                    ),
                )
                references[operation.reference] = identity
                facts.append(
                    ValuationLayer(
                        identity=identity,
                        operation_identity=operation_identity,
                        valuation_key=operation.valuation_key,
                        quantity=operation.quantity,
                        total_cost=Decimal(0),
                        source_document_identity=operation.source_document_identity,
                        source_movement_identity=operation.source_movement_identity,
                        created_at=operation.created_at,
                    )
                )
                continue

            if isinstance(operation, ConsumptionPlan):
                layer_identity = self._resolve_reference(operation, references)
                facts.append(
                    ValuationConsumption(
                        identity=self._fact_identity_factory.for_operation_fact(
                            operation_identity,
                            ValuationFactType.CONSUMPTION,
                            (
                                layer_identity,
                                operation.valuation_key,
                                operation.quantity,
                                operation.cost,
                                operation.document_identity,
                                operation.source_identity,
                                operation.created_at,
                            ),
                        ),
                        operation_identity=operation_identity,
                        valuation_key=operation.valuation_key,
                        layer_identity=layer_identity,
                        quantity=operation.quantity,
                        cost=operation.cost,
                        document_identity=operation.document_identity,
                        source_identity=operation.source_identity,
                        created_at=operation.created_at,
                    )
                )
                continue

            raise ValuationValidationError("ValuationPlan contains an unsupported operation.")

        return tuple(facts)

    @staticmethod
    def _resolve_reference(
        operation: ConsumptionPlan,
        references: dict[PlannedLayerReference, Identifier],
    ) -> Identifier:
        reference = operation.layer_reference
        if isinstance(reference, PersistedLayerReference):
            return reference.identity
        try:
            return references[reference]
        except KeyError as exc:
            raise ValuationValidationError("Planned layer reference was not resolved.") from exc
