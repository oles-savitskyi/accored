from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.valuation import (
    LayerEstablishmentPlan,
    PlannedLayerReference,
    ValuationKey,
    ValuationLayer,
    ValuationOperationIdentity,
    ValuationPlan,
)
from accore.platform.valuation.fact_builder import DefaultValuationFactBuilder

KEY = ValuationKey({"product": "PR-01"})
WHEN = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)


def test_fact_builder_is_deterministic_for_same_plan_and_operation_identity() -> None:
    document_identity = Identifier.new()
    plan = ValuationPlan(
        document_identity=document_identity,
        operations=(
            LayerEstablishmentPlan(
                reference=PlannedLayerReference(Identifier.new()),
                valuation_key=KEY,
                quantity=Decimal(10),
                source_document_identity=document_identity,
                source_movement_identity=Identifier.new(),
                created_at=WHEN,
            ),
        ),
    )
    builder = DefaultValuationFactBuilder()
    identity = ValuationOperationIdentity("establish-001")

    first = builder.build(plan, identity)
    second = builder.build(plan, identity)

    assert first == second


def test_fact_builder_changes_persistence_identity_but_not_semantics() -> None:
    document_identity = Identifier.new()
    reference = PlannedLayerReference(Identifier.new())
    plan = ValuationPlan(
        document_identity=document_identity,
        operations=(
            LayerEstablishmentPlan(
                reference=reference,
                valuation_key=KEY,
                quantity=Decimal(10),
                source_document_identity=document_identity,
                source_movement_identity=Identifier.new(),
                created_at=WHEN,
            ),
        ),
    )
    builder = DefaultValuationFactBuilder()

    first = builder.build(plan, ValuationOperationIdentity("establish-001"))[0]
    second = builder.build(plan, ValuationOperationIdentity("establish-002"))[0]

    assert isinstance(first, ValuationLayer)
    assert isinstance(second, ValuationLayer)
    assert first.identity != second.identity
    assert first.identity != second.identity
    assert first.valuation_key == second.valuation_key
    assert first.quantity == second.quantity
    assert first.total_cost == second.total_cost
    assert first.source_document_identity == second.source_document_identity
    assert first.source_movement_identity == second.source_movement_identity
    assert first.created_at == second.created_at
