from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.valuation import (
    ConsumptionPlan,
    DefaultCostTotalsEngine,
    DefaultValuationCoordinator,
    DefaultValuationPlanValidator,
    LayerEstablishmentPlan,
    PersistedLayerReference,
    PlannedLayerReference,
    ValuationConsumption,
    ValuationEstablishmentOutcome,
    ValuationFact,
    ValuationKey,
    ValuationPlan,
)
from accore.platform.valuation.errors import ValuationPersistenceError
from accore.platform.valuation.results import CostBalance, CostMovement

KEY = ValuationKey({"product": "PR-01"})
WHEN = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)


@dataclass
class FakeFactPersistence:
    facts: list[ValuationFact] = field(default_factory=list)
    fail: Exception | None = None

    def append(self, facts: Sequence[ValuationFact]) -> None:
        if self.fail:
            raise self.fail
        self.facts.extend(facts)

    def find_by_source_document(self, document_identity: Identifier) -> tuple[ValuationFact, ...]:
        return tuple(
            fact
            for fact in self.facts
            if (
                getattr(fact, "source_document_identity", None) == document_identity
                or getattr(fact, "document_identity", None) == document_identity
            )
        )

    def find_by_source_movement(self, movement_identity: Identifier) -> tuple[ValuationFact, ...]:
        return tuple(
            fact
            for fact in self.facts
            if getattr(fact, "source_movement_identity", None) == movement_identity
        )

    def find_by_valuation_key(self, valuation_key: ValuationKey) -> tuple[ValuationFact, ...]:
        return tuple(fact for fact in self.facts if fact.valuation_key == valuation_key)

    def enumerate(self) -> tuple[ValuationFact, ...]:
        return tuple(self.facts)


@dataclass
class FakeResultPersistence:
    movements: list[CostMovement] = field(default_factory=list)
    balances: dict[ValuationKey, CostBalance] = field(default_factory=dict)
    fail_on_balance: Exception | None = None

    def append_movements(self, movements: Sequence[CostMovement]) -> None:
        self.movements.extend(movements)

    def replace_balance(self, balance: CostBalance) -> None:
        if self.fail_on_balance:
            raise self.fail_on_balance
        self.balances[balance.valuation_key] = balance

    def find_movements(self, valuation_key: ValuationKey) -> tuple[CostMovement, ...]:
        return tuple(m for m in self.movements if m.valuation_key == valuation_key)

    def find_balance(self, valuation_key: ValuationKey) -> CostBalance | None:
        return self.balances.get(valuation_key)

    def enumerate_balances(self) -> tuple[CostBalance, ...]:
        return tuple(self.balances.values())


def establishment_plan() -> tuple[ValuationPlan, PlannedLayerReference]:
    reference = PlannedLayerReference(Identifier.new())
    document_identity = Identifier.new()
    return (
        ValuationPlan(
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
        ),
        reference,
    )


def coordinator(
    facts: FakeFactPersistence,
    results: FakeResultPersistence,
) -> DefaultValuationCoordinator:
    return DefaultValuationCoordinator(
        fact_persistence=facts,
        result_persistence=results,
        totals_engine=DefaultCostTotalsEngine(),
        validator=DefaultValuationPlanValidator(facts),
    )


def test_establish_layer_persists_fact_movement_and_balance() -> None:
    facts = FakeFactPersistence()
    results = FakeResultPersistence()
    plan, _ = establishment_plan()

    result = coordinator(facts, results).establish(plan)

    assert result.outcome is ValuationEstablishmentOutcome.SUCCESS
    assert len(facts.facts) == 1
    assert len(results.movements) == 1
    balance = results.find_balance(KEY)
    assert balance is not None
    assert balance.quantity == Decimal(10)
    assert balance.cost == Decimal(0)


def test_establish_resolves_planned_layer_reference() -> None:
    facts = FakeFactPersistence()
    results = FakeResultPersistence()
    plan, reference = establishment_plan()
    plan = ValuationPlan(
        document_identity=plan.document_identity,
        operations=plan.operations
        + (
            ConsumptionPlan(
                valuation_key=KEY,
                layer_reference=reference,
                quantity=Decimal(4),
                cost=Decimal(0),
                document_identity=plan.document_identity,
                source_identity=Identifier.new(),
                created_at=WHEN,
            ),
        ),
    )

    result = coordinator(facts, results).establish(plan)

    assert result.outcome is ValuationEstablishmentOutcome.SUCCESS
    consumption = facts.facts[1]
    assert isinstance(consumption, ValuationConsumption)
    assert consumption.layer_identity == facts.facts[0].identity
    balance = results.find_balance(KEY)
    assert balance is not None
    assert balance.quantity == Decimal(6)


def test_validation_failure_does_not_persist() -> None:
    facts = FakeFactPersistence()
    results = FakeResultPersistence()
    plan, reference = establishment_plan()
    invalid = ValuationPlan(
        document_identity=plan.document_identity,
        operations=plan.operations
        + (
            ConsumptionPlan(
                valuation_key=KEY,
                layer_reference=reference,
                quantity=Decimal(11),
                cost=Decimal(0),
                document_identity=plan.document_identity,
                source_identity=Identifier.new(),
                created_at=WHEN,
            ),
        ),
    )

    result = coordinator(facts, results).establish(invalid)

    assert result.outcome is ValuationEstablishmentOutcome.FAILURE
    assert facts.facts == []
    assert results.movements == []


def test_known_rollback_failure_returns_failure() -> None:
    facts = FakeFactPersistence(
        fail=ValuationPersistenceError(
            "...",
            rollback_guaranteed=True,
        )
    )
    results = FakeResultPersistence()
    plan, _ = establishment_plan()

    result = coordinator(facts, results).establish(plan)

    assert result.outcome is ValuationEstablishmentOutcome.FAILURE


def test_unknown_persistence_failure_returns_indeterminate() -> None:
    facts = FakeFactPersistence(
        fail=ValuationPersistenceError(
            "connection lost",
            rollback_guaranteed=False,
        )
    )
    results = FakeResultPersistence()
    plan, _ = establishment_plan()

    result = coordinator(facts, results).establish(plan)

    assert result.outcome is ValuationEstablishmentOutcome.INDETERMINATE


def test_result_persistence_failure_after_fact_commit_is_indeterminate() -> None:
    facts = FakeFactPersistence()
    results = FakeResultPersistence(
        fail_on_balance=ValuationPersistenceError(
            "commit status unknown",
            rollback_guaranteed=False,
        )
    )
    plan, _ = establishment_plan()

    result = coordinator(facts, results).establish(plan)

    assert result.outcome is ValuationEstablishmentOutcome.INDETERMINATE
    assert facts.facts
    assert results.movements


def test_remove_reverses_layer_and_consumption_without_mutating_history() -> None:
    facts = FakeFactPersistence()
    results = FakeResultPersistence()
    plan, reference = establishment_plan()
    plan = ValuationPlan(
        document_identity=plan.document_identity,
        operations=plan.operations
        + (
            ConsumptionPlan(
                valuation_key=KEY,
                layer_reference=reference,
                quantity=Decimal(4),
                cost=Decimal(0),
                document_identity=plan.document_identity,
                source_identity=Identifier.new(),
                created_at=WHEN,
            ),
        ),
    )

    value_coordinator = coordinator(facts, results)
    assert value_coordinator.establish(plan).outcome is ValuationEstablishmentOutcome.SUCCESS
    original_facts = tuple(facts.facts)

    removal = value_coordinator.remove(plan.document_identity)

    from accore.platform.valuation import ValuationRemovalOutcome, ValuationReversal

    assert removal.outcome is ValuationRemovalOutcome.SUCCESS
    assert tuple(facts.facts[:2]) == original_facts
    reversals = tuple(fact for fact in facts.facts[2:] if isinstance(fact, ValuationReversal))
    assert len(reversals) == 2
    assert {item.reversed_identity for item in reversals} == {
        fact.identity for fact in original_facts
    }
    assert results.find_balance(KEY) is not None
    assert results.find_balance(KEY).quantity == Decimal(0)  # type: ignore[union-attr]
    current_layers = DefaultValuationPlanValidator(facts)._current_layers()
    assert current_layers == ()


def test_remove_is_idempotent_for_already_reversed_document() -> None:
    facts = FakeFactPersistence()
    results = FakeResultPersistence()
    plan, _ = establishment_plan()
    value_coordinator = coordinator(facts, results)
    assert value_coordinator.establish(plan).outcome is ValuationEstablishmentOutcome.SUCCESS

    first = value_coordinator.remove(plan.document_identity)
    second = value_coordinator.remove(plan.document_identity)

    from accore.platform.valuation import ValuationRemovalOutcome

    assert first.outcome is ValuationRemovalOutcome.SUCCESS
    assert second.outcome is ValuationRemovalOutcome.SUCCESS
    assert len(facts.facts) == 2


def test_remove_consumption_only_restores_available_layer() -> None:
    facts = FakeFactPersistence()
    results = FakeResultPersistence()
    source_document = Identifier.new()
    layer_document = Identifier.new()
    reference_identity = Identifier.new()
    movement_identity = Identifier.new()
    layer_plan = ValuationPlan(
        document_identity=layer_document,
        operations=(
            LayerEstablishmentPlan(
                reference=PlannedLayerReference(reference_identity),
                valuation_key=KEY,
                quantity=Decimal(10),
                source_document_identity=layer_document,
                source_movement_identity=movement_identity,
                created_at=WHEN,
            ),
        ),
    )
    value_coordinator = coordinator(facts, results)
    assert value_coordinator.establish(layer_plan).outcome is ValuationEstablishmentOutcome.SUCCESS
    layer_identity = facts.facts[0].identity

    consumption_plan = ValuationPlan(
        document_identity=source_document,
        operations=(
            ConsumptionPlan(
                valuation_key=KEY,
                layer_reference=PersistedLayerReference(layer_identity),
                quantity=Decimal(4),
                cost=Decimal(0),
                document_identity=source_document,
                source_identity=Identifier.new(),
                created_at=WHEN,
            ),
        ),
    )
    assert (
        value_coordinator.establish(consumption_plan).outcome
        is ValuationEstablishmentOutcome.SUCCESS
    )

    removal = value_coordinator.remove(source_document)

    from accore.platform.valuation import ValuationRemovalOutcome

    assert removal.outcome is ValuationRemovalOutcome.SUCCESS
    current_layers = DefaultValuationPlanValidator(facts)._current_layers()
    assert len(current_layers) == 1
    assert current_layers[0].identity == layer_identity
    assert current_layers[0].quantity == Decimal(10)


def test_remove_layer_succeeds_after_consumption_from_another_document_was_reversed() -> None:
    facts = FakeFactPersistence()
    results = FakeResultPersistence()

    layer_document = Identifier.new()
    consumption_document = Identifier.new()
    reference_identity = Identifier.new()
    movement_identity = Identifier.new()

    layer_plan = ValuationPlan(
        document_identity=layer_document,
        operations=(
            LayerEstablishmentPlan(
                reference=PlannedLayerReference(reference_identity),
                valuation_key=KEY,
                quantity=Decimal(10),
                source_document_identity=layer_document,
                source_movement_identity=movement_identity,
                created_at=WHEN,
            ),
        ),
    )

    value_coordinator = coordinator(facts, results)

    assert value_coordinator.establish(layer_plan).outcome is ValuationEstablishmentOutcome.SUCCESS

    layer_identity = facts.facts[0].identity

    consumption_plan = ValuationPlan(
        document_identity=consumption_document,
        operations=(
            ConsumptionPlan(
                valuation_key=KEY,
                layer_reference=PersistedLayerReference(layer_identity),
                quantity=Decimal(4),
                cost=Decimal(0),
                document_identity=consumption_document,
                source_identity=Identifier.new(),
                created_at=WHEN,
            ),
        ),
    )

    assert (
        value_coordinator.establish(consumption_plan).outcome
        is ValuationEstablishmentOutcome.SUCCESS
    )

    consumption_identity = facts.facts[1].identity

    consumption_removal = value_coordinator.remove(consumption_document)

    from accore.platform.valuation import ValuationRemovalOutcome

    assert consumption_removal.outcome is ValuationRemovalOutcome.SUCCESS

    layer_removal = value_coordinator.remove(layer_document)

    assert layer_removal.outcome is ValuationRemovalOutcome.SUCCESS

    from accore.platform.valuation import ValuationReversal

    reversals = tuple(fact for fact in facts.facts if isinstance(fact, ValuationReversal))

    assert {reversal.reversed_identity for reversal in reversals} == {
        consumption_identity,
        layer_identity,
    }
