from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.valuation import (
    CostBalance,
    CostMovement,
    DefaultCostTotalsEngine,
    DefaultValuationCostMovementIdentityFactory,
    DefaultValuationFactToCostMovementProjector,
    DefaultValuationRebuilder,
    ValuationAllocation,
    ValuationCostMovementRole,
    ValuationFact,
    ValuationFactPersistence,
    ValuationKey,
    ValuationLayer,
    ValuationRebuildOutcome,
    ValuationReversal,
)

KEY = ValuationKey({"product": "PR-01"})
WHEN = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)


class FakeFacts(ValuationFactPersistence):
    def __init__(self, facts: Sequence[ValuationFact] = ()) -> None:
        self.facts = list(facts)

    def append(self, facts: Sequence[ValuationFact]) -> None:
        self.facts.extend(facts)

    def find(self, identity: Identifier) -> ValuationFact | None:
        return next((fact for fact in self.facts if fact.identity == identity), None)

    def find_by_source_document(self, document_identity: Identifier) -> tuple[ValuationFact, ...]:
        return ()

    def find_by_source_movement(self, movement_identity: Identifier) -> tuple[ValuationFact, ...]:
        return ()

    def find_by_valuation_key(self, valuation_key: ValuationKey) -> tuple[ValuationFact, ...]:
        return tuple(fact for fact in self.facts if fact.valuation_key == valuation_key)

    def enumerate(self) -> tuple[ValuationFact, ...]:
        return tuple(self.facts)


class FakeResults:
    def __init__(self) -> None:
        self.movements: list[CostMovement] = []
        self.balances: dict[ValuationKey, CostBalance] = {}

    def append_movements(self, movements: Sequence[CostMovement]) -> None:
        self.movements.extend(movements)

    def find_movement(self, identity: Identifier) -> CostMovement | None:
        return next(
            (movement for movement in self.movements if movement.identity == identity),
            None,
        )

    def find_movements(self, valuation_key: ValuationKey) -> tuple[CostMovement, ...]:
        return tuple(m for m in self.movements if m.valuation_key == valuation_key)

    def enumerate_movements(self) -> tuple[CostMovement, ...]:
        return tuple(self.movements)

    def reconcile_movements(self, movements: Sequence[CostMovement]) -> None:
        from accore.platform.valuation import ValuationConflictError

        current = {movement.identity: movement for movement in self.movements}
        expected = {}
        for movement in movements:
            existing = expected.get(movement.identity)
            if existing is not None and existing != movement:
                raise ValuationConflictError("conflict")
            persisted = current.get(movement.identity)
            if persisted is not None and persisted != movement:
                raise ValuationConflictError("conflict")
            expected[movement.identity] = movement
        self.movements = list(expected.values())

    def replace_balance(self, balance: CostBalance) -> None:
        self.balances[balance.valuation_key] = balance

    def find_balance(self, valuation_key: ValuationKey) -> CostBalance | None:
        return self.balances.get(valuation_key)

    def enumerate_balances(self) -> tuple[CostBalance, ...]:
        return tuple(self.balances.values())


def ident() -> Identifier:
    return Identifier.new()


def layer() -> ValuationLayer:
    return ValuationLayer(
        identity=ident(),
        valuation_key=KEY,
        quantity=Decimal(100),
        total_cost=Decimal(1000),
        source_document_identity=ident(),
        source_movement_identity=ident(),
        created_at=WHEN,
    )


def test_movement_identity_is_deterministic() -> None:
    factory = DefaultValuationCostMovementIdentityFactory()
    fact = layer()

    assert factory.create(fact, ValuationCostMovementRole.ORIGINAL) == factory.create(
        fact, ValuationCostMovementRole.ORIGINAL
    )
    assert factory.create(fact, ValuationCostMovementRole.ORIGINAL) != factory.create(
        fact, ValuationCostMovementRole.REVERSAL
    )


def test_projector_reversal_keeps_original_and_adds_compensation() -> None:
    original = layer()
    reversal = ValuationReversal(
        identity=ident(),
        reversed_identity=original.identity,
        valuation_key=KEY,
        document_identity=ident(),
        source_identity=ident(),
        created_at=WHEN,
    )
    facts = FakeFacts((original, reversal))
    projector = DefaultValuationFactToCostMovementProjector()

    original_movement = projector.project(original, facts)[0]
    reversal_movement = projector.project(reversal, facts)[0]

    assert original_movement.quantity == Decimal(100)
    assert original_movement.cost == Decimal(1000)
    assert reversal_movement.quantity == Decimal(-100)
    assert reversal_movement.cost == Decimal(-1000)
    assert original_movement.identity != reversal_movement.identity


def test_rebuild_is_idempotent_and_preserves_historical_movements() -> None:
    original = layer()
    reversal = ValuationReversal(
        identity=ident(),
        reversed_identity=original.identity,
        valuation_key=KEY,
        document_identity=ident(),
        source_identity=ident(),
        created_at=WHEN,
    )
    facts = FakeFacts((reversal, original))
    results = FakeResults()
    rebuilder = DefaultValuationRebuilder(
        fact_persistence=facts,
        result_persistence=results,
        totals_engine=DefaultCostTotalsEngine(),
    )

    first = rebuilder.rebuild()
    first_movements = results.enumerate_movements()
    second = rebuilder.rebuild()

    assert first.outcome is ValuationRebuildOutcome.SUCCESS
    assert second.outcome is ValuationRebuildOutcome.SUCCESS
    assert results.enumerate_movements() == first_movements
    assert len(results.find_movements(KEY)) == 2
    balance = results.find_balance(KEY)
    assert balance is not None
    assert balance.quantity == Decimal(0)
    assert balance.cost == Decimal(0)


def test_rebuild_detects_conflicting_persisted_movement() -> None:
    original = layer()
    facts = FakeFacts((original,))
    results = FakeResults()
    projector = DefaultValuationFactToCostMovementProjector()
    expected = projector.project(original, facts)[0]
    results.movements.append(
        CostMovement(
            identity=expected.identity,
            valuation_key=expected.valuation_key,
            quantity=expected.quantity + Decimal(1),
            cost=expected.cost,
            source_identity=expected.source_identity,
            created_at=expected.created_at,
        )
    )

    result = DefaultValuationRebuilder(
        fact_persistence=facts,
        result_persistence=results,
        totals_engine=DefaultCostTotalsEngine(),
    ).rebuild()

    assert result.outcome is ValuationRebuildOutcome.FAILURE


def test_rebuild_removes_stale_derived_movement() -> None:
    original = layer()
    facts = FakeFacts((original,))
    results = FakeResults()
    results.movements.append(
        CostMovement(
            identity=ident(),
            valuation_key=KEY,
            quantity=Decimal(1),
            cost=Decimal(1),
            source_identity=ident(),
            created_at=WHEN,
        )
    )

    result = DefaultValuationRebuilder(
        fact_persistence=facts,
        result_persistence=results,
        totals_engine=DefaultCostTotalsEngine(),
    ).rebuild()

    assert result.outcome is ValuationRebuildOutcome.SUCCESS
    assert len(results.find_movements(KEY)) == 1
    assert results.find_movements(KEY)[0].quantity == Decimal(100)


def test_full_rebuild_reconstructs_stale_balance_for_empty_key() -> None:
    results = FakeResults()
    stale_key = ValuationKey({"product": "STALE"})
    results.balances[stale_key] = CostBalance(
        valuation_key=stale_key,
        quantity=Decimal(10),
        cost=Decimal(100),
        calculated_at=WHEN,
    )

    result = DefaultValuationRebuilder(
        fact_persistence=FakeFacts(),
        result_persistence=results,
        totals_engine=DefaultCostTotalsEngine(),
    ).rebuild()

    assert result.outcome is ValuationRebuildOutcome.SUCCESS
    balance = results.find_balance(stale_key)
    assert balance is not None
    assert balance.quantity == Decimal(0)
    assert balance.cost == Decimal(0)


def test_allocation_projects_cost_without_quantity() -> None:
    allocation = ValuationAllocation(
        identity=ident(),
        adjustment_identity=ident(),
        layer_identity=ident(),
        valuation_key=KEY,
        amount=Decimal(125),
        created_at=WHEN,
    )
    movement = DefaultValuationFactToCostMovementProjector().project(
        allocation,
        FakeFacts((allocation,)),
    )[0]

    assert movement.quantity == Decimal(0)
    assert movement.cost == Decimal(125)
