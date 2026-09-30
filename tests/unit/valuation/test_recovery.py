from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.persistence import PersistenceIndeterminateError
from accore.platform.valuation import (
    LayerEstablishmentPlan,
    PlannedLayerReference,
    ValuationConflictError,
    ValuationEstablishRecoveryDescriptor,
    ValuationFact,
    ValuationFactRecoveryOutcome,
    ValuationFactRecoveryService,
    ValuationKey,
    ValuationLayer,
    ValuationOperationIdentity,
    ValuationOperationRecord,
    ValuationOperationType,
)

KEY = ValuationKey({"product": "PR-01"})
WHEN = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)


def _id() -> Identifier:
    return Identifier.new()


def _layer(identity: Identifier | None = None) -> ValuationLayer:
    return ValuationLayer(
        identity=identity or _id(),
        valuation_key=KEY,
        quantity=Decimal(10),
        total_cost=Decimal(0),
        source_document_identity=_id(),
        source_movement_identity=_id(),
        created_at=WHEN,
        operation_identity=ValuationOperationIdentity("operation-001"),
    )


def _operation() -> ValuationOperationRecord:
    document_identity = _id()
    descriptor = ValuationEstablishRecoveryDescriptor(
        document_identity=document_identity,
        operations=(
            LayerEstablishmentPlan(
                reference=PlannedLayerReference(_id()),
                valuation_key=KEY,
                quantity=Decimal(10),
                source_document_identity=document_identity,
                source_movement_identity=_id(),
                created_at=WHEN,
            ),
        ),
    )
    return ValuationOperationRecord(
        identity=ValuationOperationIdentity("operation-001"),
        operation_type=ValuationOperationType.ESTABLISH,
        document_identity=document_identity,
        fingerprint="fingerprint",
        establish_descriptor=descriptor,
    )


class RecoveryPersistence:
    def __init__(self, facts: tuple[ValuationFact, ...] = ()) -> None:
        self.facts = list(facts)
        self.append_calls: list[tuple[ValuationFact, ...]] = []
        self.append_error: Exception | None = None
        self.find_error: Exception | None = None

    def find(self, identity: Identifier) -> ValuationFact | None:
        if self.find_error is not None:
            raise self.find_error
        return next((fact for fact in self.facts if fact.identity == identity), None)

    def append(self, facts: tuple[ValuationFact, ...]) -> None:
        self.append_calls.append(facts)
        if self.append_error is not None:
            error = self.append_error
            self.append_error = None
            raise error
        self.facts.extend(facts)


def test_recovery_succeeds_when_all_expected_facts_exist() -> None:
    first = _layer()
    second = _layer()
    persistence = RecoveryPersistence((first, second))
    service = ValuationFactRecoveryService(fact_persistence=persistence)

    result = service.reconcile(_operation(), (first, second))

    assert result.outcome is ValuationFactRecoveryOutcome.SUCCESS
    assert persistence.append_calls == []


def test_recovery_appends_only_missing_facts() -> None:
    first = _layer()
    second = _layer()
    persistence = RecoveryPersistence((first,))
    service = ValuationFactRecoveryService(fact_persistence=persistence)

    result = service.reconcile(_operation(), (first, second))

    assert result.outcome is ValuationFactRecoveryOutcome.SUCCESS
    assert persistence.append_calls == [(second,)]
    assert persistence.facts == [first, second]


def test_recovery_rejects_semantic_conflict() -> None:
    identity = _id()
    existing = _layer(identity)
    conflicting = ValuationLayer(
        identity=identity,
        valuation_key=KEY,
        quantity=Decimal(99),
        total_cost=Decimal(0),
        source_document_identity=existing.source_document_identity,
        source_movement_identity=existing.source_movement_identity,
        created_at=WHEN,
        operation_identity=existing.operation_identity,
    )
    persistence = RecoveryPersistence((existing,))
    service = ValuationFactRecoveryService(fact_persistence=persistence)

    result = service.reconcile(_operation(), (conflicting,))

    assert result.outcome is ValuationFactRecoveryOutcome.FAILURE
    assert isinstance(result.error, ValuationConflictError)
    assert persistence.append_calls == []


def test_recovery_reconciles_indeterminate_append_when_facts_are_present() -> None:
    first = _layer()
    persistence = RecoveryPersistence()
    persistence.append_error = PersistenceIndeterminateError("unknown")

    original_append = persistence.append

    def append_and_persist_then_fail(facts: tuple[ValuationFact, ...]) -> None:
        persistence.append_calls.append(facts)
        persistence.facts.extend(facts)
        raise PersistenceIndeterminateError("unknown")

    persistence.append = append_and_persist_then_fail  # type: ignore[method-assign]
    service = ValuationFactRecoveryService(fact_persistence=persistence)

    result = service.reconcile(_operation(), (first,))

    assert result.outcome is ValuationFactRecoveryOutcome.SUCCESS
    assert persistence.append_calls == [(first,)]
    assert persistence.facts == [first]
    del original_append


def test_recovery_retries_only_remaining_missing_facts() -> None:
    first = _layer()
    second = _layer()
    persistence = RecoveryPersistence()
    calls = 0

    def append(facts: tuple[ValuationFact, ...]) -> None:
        nonlocal calls
        calls += 1
        persistence.append_calls.append(facts)
        if calls == 1:
            persistence.facts.append(first)
            raise PersistenceIndeterminateError("partial")
        persistence.facts.extend(facts)

    persistence.append = append  # type: ignore[method-assign]
    service = ValuationFactRecoveryService(fact_persistence=persistence)

    result = service.reconcile(_operation(), (first, second))

    assert result.outcome is ValuationFactRecoveryOutcome.SUCCESS
    assert persistence.append_calls == [(first, second), (second,)]
    assert persistence.facts == [first, second]


def test_recovery_remains_indeterminate_when_authoritative_read_fails() -> None:
    first = _layer()
    persistence = RecoveryPersistence()
    persistence.find_error = PersistenceIndeterminateError("read failed")
    service = ValuationFactRecoveryService(fact_persistence=persistence)

    result = service.reconcile(_operation(), (first,))

    assert result.outcome is ValuationFactRecoveryOutcome.INDETERMINATE
    assert isinstance(result.error, PersistenceIndeterminateError)
