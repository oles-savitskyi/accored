from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.persistence import PersistenceIndeterminateError
from accore.platform.valuation import (
    ConsumptionPlan,
    DefaultCostTotalsEngine,
    DefaultValuationCoordinator,
    DefaultValuationFactIdentityFactory,
    DefaultValuationFactToCostMovementProjector,
    DefaultValuationPlanValidator,
    DefaultValuationRebuilder,
    LayerEstablishmentPlan,
    PersistedLayerReference,
    PlannedLayerReference,
    ValuationConflictError,
    ValuationConsumption,
    ValuationEstablishmentOutcome,
    ValuationFact,
    ValuationFactType,
    ValuationKey,
    ValuationLayer,
    ValuationOperationIdentity,
    ValuationOperationRecord,
    ValuationOperationType,
    ValuationPlan,
    ValuationRecoveryOutcome,
    ValuationRemovalOutcome,
    ValuationReversal,
)
from accore.platform.valuation.coordinator import (
    _canonical_remove_target_identities,
    _remove_fingerprint,
)
from accore.platform.valuation.errors import ValuationPersistenceError
from accore.platform.valuation.results import CostBalance, CostMovement

KEY = ValuationKey({"product": "PR-01"})
WHEN = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)


class FakeOperationPersistence:
    def __init__(
        self,
        *,
        append_error: Exception | None = None,
        reconciliation_operation: ValuationOperationRecord | None = None,
        reconciliation_error: Exception | None = None,
    ) -> None:
        self.operations: list[ValuationOperationRecord] = []
        self.append_calls: list[ValuationOperationRecord] = []
        self.find_calls: list[ValuationOperationIdentity] = []
        self.append_error = append_error
        self.reconciliation_operation = reconciliation_operation
        self.reconciliation_error = reconciliation_error

    def append(self, operation: ValuationOperationRecord) -> None:
        self.append_calls.append(operation)

        if self.append_error is not None:
            error = self.append_error
            self.append_error = None
            raise error

        self.operations.append(operation)

    def find(
        self,
        identity: ValuationOperationIdentity,
    ) -> ValuationOperationRecord | None:
        self.find_calls.append(identity)

        if self.reconciliation_error is not None:
            raise self.reconciliation_error

        if self.reconciliation_operation is not None:
            return self.reconciliation_operation

        return next(
            (operation for operation in self.operations if operation.identity == identity),
            None,
        )

    def find_by_document(
        self,
        document_identity: Identifier,
    ) -> tuple[ValuationOperationRecord, ...]:
        return tuple(
            operation
            for operation in self.operations
            if operation.document_identity == document_identity
        )

    def enumerate(self) -> tuple[ValuationOperationRecord, ...]:
        return tuple(self.operations)


@dataclass
class FakeFactPersistence:
    facts: list[ValuationFact] = field(default_factory=list)
    fail: Exception | None = None

    def append(self, facts: Sequence[ValuationFact]) -> None:
        if self.fail:
            raise self.fail
        self.facts.extend(facts)

    def find(self, identity: Identifier) -> ValuationFact | None:
        return next((fact for fact in self.facts if fact.identity == identity), None)

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

    def reconcile_movements(self, movements: Sequence[CostMovement]) -> None:
        self.movements = list(movements)

    def enumerate_movements(self) -> tuple[CostMovement, ...]:
        return tuple(self.movements)

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
    fact_persistence: FakeFactPersistence | None = None,
    result_persistence: FakeResultPersistence | None = None,
    operation_persistence: FakeOperationPersistence | None = None,
) -> DefaultValuationCoordinator:
    facts = fact_persistence or FakeFactPersistence()
    results = result_persistence or FakeResultPersistence()
    totals_engine = DefaultCostTotalsEngine()
    return DefaultValuationCoordinator(
        fact_persistence=facts,
        result_persistence=results,
        operation_persistence=operation_persistence or FakeOperationPersistence(),
        totals_engine=totals_engine,
        validator=DefaultValuationPlanValidator(facts),
        rebuilder=DefaultValuationRebuilder(
            fact_persistence=facts,
            result_persistence=results,
            totals_engine=totals_engine,
        ),
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


def test_establish_uses_deterministic_fact_identity() -> None:
    facts = FakeFactPersistence()
    operations = FakeOperationPersistence()
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

    result = coordinator(
        facts,
        result_persistence=results,
        operation_persistence=operations,
    ).establish(plan)

    assert result.outcome is ValuationEstablishmentOutcome.SUCCESS
    operation = operations.operations[0]
    layer, consumption = facts.facts
    factory = DefaultValuationFactIdentityFactory()

    assert layer.operation_identity == operation.identity
    assert consumption.operation_identity == operation.identity

    assert layer.identity == factory.for_operation_fact(
        operation.identity,
        ValuationFactType.LAYER,
        (
            plan.operations[0].valuation_key,
            plan.operations[0].quantity,
            plan.operations[0].source_document_identity,
            plan.operations[0].source_movement_identity,
            plan.operations[0].created_at,
        ),
    )
    assert consumption.identity == factory.for_operation_fact(
        operation.identity,
        ValuationFactType.CONSUMPTION,
        (
            layer.identity,
            plan.operations[1].valuation_key,
            plan.operations[1].quantity,
            plan.operations[1].cost,
            plan.operations[1].document_identity,
            plan.operations[1].source_identity,
            plan.operations[1].created_at,
        ),
    )

    projected = DefaultValuationFactToCostMovementProjector().project(consumption, facts)[0]
    assert results.movements[1].identity == projected.identity


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


def test_remove_target_identities_have_canonical_order() -> None:
    first = Identifier.from_str("01M3PHV4M6TET9KF074HS598DZ")
    second = Identifier.from_str("01M3PHV4M6501PVDY0BXD65MYA")
    third = Identifier.from_str("01M3PHV4M6V5N3R8K3Q4YQ9W1Z")

    canonical = _canonical_remove_target_identities((third, first, second))

    assert canonical == (second, first, third)
    assert _canonical_remove_target_identities((second, third, first)) == canonical


def test_remove_target_fingerprint_is_independent_of_fact_enumeration_order() -> None:
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

    ordered_facts = tuple(facts.facts)
    operation_persistence_a = FakeOperationPersistence()
    operation_persistence_b = FakeOperationPersistence()

    result_a = coordinator(
        FakeFactPersistence(facts=list(ordered_facts)),
        FakeResultPersistence(),
        operation_persistence_a,
    ).remove(plan.document_identity)
    result_b = coordinator(
        FakeFactPersistence(facts=list(reversed(ordered_facts))),
        FakeResultPersistence(),
        operation_persistence_b,
    ).remove(plan.document_identity)

    assert result_a.outcome is ValuationRemovalOutcome.SUCCESS
    assert result_b.outcome is ValuationRemovalOutcome.SUCCESS
    assert len(operation_persistence_a.operations) == 1
    assert len(operation_persistence_b.operations) == 1
    assert (
        operation_persistence_a.operations[0].fingerprint
        == operation_persistence_b.operations[0].fingerprint
    )


def test_remove_target_fingerprint_contains_canonical_target_order() -> None:
    document_identity = Identifier.new()
    first_identity = Identifier.new()
    second_identity = Identifier.new()

    first = ValuationLayer(
        identity=first_identity,
        valuation_key=KEY,
        quantity=Decimal(10),
        total_cost=Decimal(0),
        source_document_identity=document_identity,
        source_movement_identity=Identifier.new(),
        created_at=WHEN,
    )
    second = ValuationLayer(
        identity=second_identity,
        valuation_key=KEY,
        quantity=Decimal(5),
        total_cost=Decimal(0),
        source_document_identity=document_identity,
        source_movement_identity=Identifier.new(),
        created_at=WHEN,
    )

    facts = FakeFactPersistence(facts=[second, first])
    operation_persistence = FakeOperationPersistence()

    result = coordinator(
        facts,
        FakeResultPersistence(),
        operation_persistence,
    ).remove(document_identity)

    assert result.outcome is ValuationRemovalOutcome.SUCCESS
    assert len(operation_persistence.operations) == 1

    target_identities = _canonical_remove_target_identities((first_identity, second_identity))

    assert operation_persistence.operations[0].fingerprint == _remove_fingerprint(
        document_identity,
        target_identities,
    )


def test_remove_duplicate_target_identity_is_failure() -> None:
    document_identity = Identifier.new()
    duplicate_identity = Identifier.new()
    duplicate = ValuationLayer(
        identity=duplicate_identity,
        valuation_key=KEY,
        quantity=Decimal(10),
        total_cost=Decimal(0),
        source_document_identity=document_identity,
        source_movement_identity=Identifier.new(),
        created_at=WHEN,
    )
    facts = FakeFactPersistence(facts=[duplicate, duplicate])
    operation_persistence = FakeOperationPersistence()

    result = coordinator(
        facts,
        FakeResultPersistence(),
        operation_persistence,
    ).remove(document_identity)

    assert result.outcome is ValuationRemovalOutcome.FAILURE
    assert operation_persistence.operations == []
    assert operation_persistence.append_calls == []


def test_remove_excludes_already_reversed_targets() -> None:
    document_identity = Identifier.new()
    layer_identity = Identifier.new()
    layer = ValuationLayer(
        identity=layer_identity,
        valuation_key=KEY,
        quantity=Decimal(10),
        total_cost=Decimal(0),
        source_document_identity=document_identity,
        source_movement_identity=Identifier.new(),
        created_at=WHEN,
    )
    reversal = ValuationReversal(
        identity=Identifier.new(),
        reversed_identity=layer_identity,
        valuation_key=KEY,
        document_identity=document_identity,
        source_identity=layer.source_movement_identity,
        created_at=WHEN,
    )
    operation_persistence = FakeOperationPersistence()

    result = coordinator(
        FakeFactPersistence(facts=[layer, reversal]),
        FakeResultPersistence(),
        operation_persistence,
    ).remove(document_identity)

    assert result.outcome is ValuationRemovalOutcome.SUCCESS
    assert len(operation_persistence.operations) == 1
    assert operation_persistence.operations[0].fingerprint == _remove_fingerprint(
        document_identity,
        (),
    )


def test_remove_target_set_is_fixed_after_operation_registration() -> None:
    document_identity = Identifier.new()
    first_identity = Identifier.new()
    second_identity = Identifier.new()
    first = ValuationLayer(
        identity=first_identity,
        valuation_key=KEY,
        quantity=Decimal(10),
        total_cost=Decimal(0),
        source_document_identity=document_identity,
        source_movement_identity=Identifier.new(),
        created_at=WHEN,
    )
    second = ValuationLayer(
        identity=second_identity,
        valuation_key=KEY,
        quantity=Decimal(5),
        total_cost=Decimal(0),
        source_document_identity=document_identity,
        source_movement_identity=Identifier.new(),
        created_at=WHEN,
    )
    facts = FakeFactPersistence(facts=[first])

    class MutatingOperationPersistence(FakeOperationPersistence):
        def append(self, operation: ValuationOperationRecord) -> None:
            super().append(operation)
            if len(self.operations) == 1:
                facts.facts.append(second)

    operation_persistence = MutatingOperationPersistence()
    result = coordinator(
        facts,
        FakeResultPersistence(),
        operation_persistence,
    ).remove(document_identity)

    assert result.outcome is ValuationRemovalOutcome.SUCCESS
    assert len(operation_persistence.operations) == 1
    assert len(facts.facts) == 3
    assert any(
        isinstance(fact, ValuationReversal) and fact.reversed_identity == first_identity
        for fact in facts.facts
    )
    assert not any(
        isinstance(fact, ValuationReversal) and fact.reversed_identity == second_identity
        for fact in facts.facts
    )
    reversals = tuple(fact for fact in facts.facts if isinstance(fact, ValuationReversal))

    assert len(reversals) == 1
    assert reversals[0].reversed_identity == first_identity


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


class PartialIndeterminateFactPersistence(FakeFactPersistence):
    def __init__(self) -> None:
        super().__init__()
        self.append_calls: list[tuple[ValuationFact, ...]] = []

    def append(self, facts: Sequence[ValuationFact]) -> None:
        self.append_calls.append(tuple(facts))
        if len(self.append_calls) == 1:
            self.facts.append(facts[0])
            raise PersistenceIndeterminateError("partial fact append")
        super().append(facts)


def test_establish_recovers_partially_persisted_facts() -> None:
    facts = PartialIndeterminateFactPersistence()
    valuation_coordinator = coordinator(fact_persistence=facts)

    plan, _ = establishment_plan()
    result = valuation_coordinator.establish(plan)

    assert result.outcome is ValuationEstablishmentOutcome.SUCCESS
    assert len(facts.facts) == 1
    assert len(facts.append_calls) == 1


def test_remove_recovers_partially_persisted_reversal_facts() -> None:
    class RemoveRecoveryFactPersistence(FakeFactPersistence):
        def __init__(self) -> None:
            super().__init__()
            self.append_calls: list[tuple[ValuationFact, ...]] = []
            self._append_count = 0

        def append(self, facts: Sequence[ValuationFact]) -> None:
            self.append_calls.append(tuple(facts))
            self._append_count += 1
            if self._append_count == 2:
                self.facts.append(facts[0])
                raise PersistenceIndeterminateError("partial reversal append")
            super().append(facts)

    facts = RemoveRecoveryFactPersistence()
    operations = FakeOperationPersistence()
    valuation_coordinator = coordinator(
        fact_persistence=facts,
        operation_persistence=operations,
    )

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
            LayerEstablishmentPlan(
                reference=PlannedLayerReference(Identifier.new()),
                valuation_key=KEY,
                quantity=Decimal(5),
                source_document_identity=document_identity,
                source_movement_identity=Identifier.new(),
                created_at=WHEN,
            ),
        ),
    )

    established = valuation_coordinator.establish(plan)
    assert established.outcome is ValuationEstablishmentOutcome.SUCCESS

    removed = valuation_coordinator.remove(document_identity)

    assert removed.outcome is ValuationRemovalOutcome.SUCCESS
    assert len(facts.append_calls) == 3
    assert len(facts.facts) == 4
    reversals = tuple(fact for fact in facts.facts if isinstance(fact, ValuationReversal))
    assert len(reversals) == 2
    assert len({reversal.reversed_identity for reversal in reversals}) == 2
    remove_operations = tuple(
        operation
        for operation in operations.operations
        if operation.operation_type.value == "remove"
    )
    assert len(remove_operations) == 1
    assert remove_operations[0].target_fact_identities == tuple(
        sorted((reversal.reversed_identity for reversal in reversals), key=str)
    )


def test_establish_persists_operation_before_facts() -> None:
    events: list[str] = []

    class OrderedOperationPersistence(FakeOperationPersistence):
        def append(self, operation):
            events.append("operation")
            super().append(operation)

    class OrderedFactPersistence(FakeFactPersistence):
        def append(self, facts):
            events.append("facts")
            super().append(facts)

    operation_persistence = OrderedOperationPersistence()
    fact_persistence = OrderedFactPersistence()

    valuation_coordinator = coordinator(
        fact_persistence=fact_persistence,
        operation_persistence=operation_persistence,
    )

    plan, _ = establishment_plan()
    result = valuation_coordinator.establish(plan)

    assert result.outcome is ValuationEstablishmentOutcome.SUCCESS
    assert events == ["operation", "facts"]
    assert len(operation_persistence.operations) == 1
    assert len(fact_persistence.facts) == 1


def test_establish_operation_persistence_failure_does_not_persist_facts() -> None:
    operation_persistence = FakeOperationPersistence(
        append_error=ValuationConflictError(
            "operation already exists with different semantics",
        ),
    )
    fact_persistence = FakeFactPersistence()

    valuation_coordinator = coordinator(
        fact_persistence=fact_persistence,
        operation_persistence=operation_persistence,
    )

    plan, _ = establishment_plan()
    result = valuation_coordinator.establish(plan)

    assert result.outcome is ValuationEstablishmentOutcome.FAILURE
    assert isinstance(result.error, ValuationConflictError)

    assert len(operation_persistence.append_calls) == 1
    assert fact_persistence.facts == []


class IndeterminateExistingOperationPersistence(FakeOperationPersistence):
    def append(self, operation: ValuationOperationRecord) -> None:
        self.append_calls.append(operation)

        if len(self.append_calls) == 1:
            self.reconciliation_operation = operation
            raise PersistenceIndeterminateError(
                "operation append outcome is indeterminate",
            )

        self.operations.append(operation)


def test_establish_operation_indeterminate_reconciles_existing_operation() -> None:
    operation_persistence = IndeterminateExistingOperationPersistence()
    fact_persistence = FakeFactPersistence()

    valuation_coordinator = coordinator(
        fact_persistence=fact_persistence,
        operation_persistence=operation_persistence,
    )

    plan, _ = establishment_plan()
    result = valuation_coordinator.establish(plan)

    assert result.outcome is ValuationEstablishmentOutcome.SUCCESS
    assert result.error is None

    assert len(operation_persistence.append_calls) == 1
    assert len(operation_persistence.find_calls) == 1
    assert operation_persistence.find_calls[0] == operation_persistence.append_calls[0].identity

    assert len(fact_persistence.facts) == 1


class IndeterminateNotFoundOperationPersistence(FakeOperationPersistence):
    def append(self, operation: ValuationOperationRecord) -> None:
        self.append_calls.append(operation)

        if len(self.append_calls) == 1:
            raise PersistenceIndeterminateError(
                "operation append outcome is indeterminate",
            )

        self.operations.append(operation)


def test_establish_operation_indeterminate_retries_when_not_found() -> None:
    operation_persistence = IndeterminateNotFoundOperationPersistence()
    fact_persistence = FakeFactPersistence()

    valuation_coordinator = coordinator(
        fact_persistence=fact_persistence,
        operation_persistence=operation_persistence,
    )

    plan, _ = establishment_plan()
    result = valuation_coordinator.establish(plan)

    assert result.outcome is ValuationEstablishmentOutcome.SUCCESS
    assert result.error is None

    assert len(operation_persistence.append_calls) == 2
    assert len(operation_persistence.find_calls) == 1

    first_operation = operation_persistence.append_calls[0]
    second_operation = operation_persistence.append_calls[1]

    assert second_operation == first_operation
    assert fact_persistence.facts != []


def test_establish_operation_indeterminate_stays_indeterminate_when_reconciliation_fails() -> None:
    operation_persistence = FakeOperationPersistence(
        append_error=PersistenceIndeterminateError(
            "operation append outcome is indeterminate",
        ),
        reconciliation_error=PersistenceIndeterminateError(
            "operation reconciliation is indeterminate",
        ),
    )
    fact_persistence = FakeFactPersistence()

    valuation_coordinator = coordinator(
        fact_persistence=fact_persistence,
        operation_persistence=operation_persistence,
    )

    plan, _ = establishment_plan()
    result = valuation_coordinator.establish(plan)

    assert result.outcome is ValuationEstablishmentOutcome.INDETERMINATE
    assert isinstance(result.error, PersistenceIndeterminateError)

    assert len(operation_persistence.append_calls) == 1
    assert len(operation_persistence.find_calls) == 1

    assert fact_persistence.facts == []


def test_recover_exposes_operation_level_remove_recovery() -> None:
    facts = FakeFactPersistence()
    operations = FakeOperationPersistence()
    document_identity = Identifier.new()
    layer = ValuationLayer(
        identity=Identifier.new(),
        valuation_key=KEY,
        quantity=Decimal(10),
        total_cost=Decimal(100),
        source_document_identity=document_identity,
        source_movement_identity=Identifier.new(),
        created_at=WHEN,
        operation_identity=ValuationOperationIdentity("establish-001"),
    )
    operation = ValuationOperationRecord(
        identity=ValuationOperationIdentity("remove-001"),
        operation_type=ValuationOperationType.REMOVE,
        document_identity=document_identity,
        fingerprint="fingerprint",
        target_fact_identities=(layer.identity,),
    )
    facts.facts.append(layer)
    operations.operations.append(operation)
    valuation_coordinator = coordinator(
        fact_persistence=facts,
        operation_persistence=operations,
    )

    result = valuation_coordinator.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.SUCCESS
    reversals = tuple(fact for fact in facts.facts if isinstance(fact, ValuationReversal))
    assert len(reversals) == 1
    assert reversals[0].reversed_identity == layer.identity
