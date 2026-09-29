from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.persistence import PersistenceIndeterminateError
from accore.platform.valuation import (
    DefaultValuationFactIdentityFactory,
    DefaultValuationOperationRecoveryService,
    ValuationFact,
    ValuationFactRecoveryService,
    ValuationKey,
    ValuationLayer,
    ValuationNotFoundError,
    ValuationOperationIdentity,
    ValuationOperationRecord,
    ValuationOperationType,
    ValuationRecoveryOutcome,
    ValuationReversal,
)

KEY = ValuationKey({"product": "PR-01"})
WHEN = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)


def _id() -> Identifier:
    return Identifier.new()


def _layer(identity: Identifier | None = None) -> ValuationLayer:
    return ValuationLayer(
        identity=identity or _id(),
        valuation_key=KEY,
        quantity=Decimal(10),
        total_cost=Decimal(100),
        source_document_identity=_id(),
        source_movement_identity=_id(),
        created_at=WHEN,
        operation_identity=ValuationOperationIdentity("establish-001"),
    )


def _operation(targets: tuple[Identifier, ...]) -> ValuationOperationRecord:
    return ValuationOperationRecord(
        identity=ValuationOperationIdentity("remove-001"),
        operation_type=ValuationOperationType.REMOVE,
        document_identity=_id(),
        fingerprint="fingerprint",
        target_fact_identities=targets,
    )


class OperationPersistence:
    def __init__(self, operation: ValuationOperationRecord | None = None) -> None:
        self.operation = operation
        self.find_error: Exception | None = None
        self.find_calls: list[ValuationOperationIdentity] = []

    def append(self, operation: ValuationOperationRecord) -> None:
        self.operation = operation

    def find(self, identity: ValuationOperationIdentity) -> ValuationOperationRecord | None:
        self.find_calls.append(identity)
        if self.find_error is not None:
            raise self.find_error
        if self.operation is not None and self.operation.identity == identity:
            return self.operation
        return None

    def find_by_document(
        self, document_identity: Identifier
    ) -> tuple[ValuationOperationRecord, ...]:
        if self.operation is not None and self.operation.document_identity == document_identity:
            return (self.operation,)
        return ()

    def enumerate(self) -> tuple[ValuationOperationRecord, ...]:
        return (self.operation,) if self.operation is not None else ()


class FactPersistence:
    def __init__(self, facts: tuple[ValuationFact, ...] = ()) -> None:
        self.facts: list[ValuationFact] = list(facts)
        self.append_calls: list[tuple[ValuationFact, ...]] = []
        self.find_errors: dict[Identifier, Exception] = {}

    def append(self, facts: Sequence[ValuationFact]) -> None:
        self.append_calls.append(tuple(facts))
        for fact in facts:
            if fact not in self.facts:
                self.facts.append(fact)

    def find(self, identity: Identifier) -> ValuationFact | None:
        error = self.find_errors.get(identity)
        if error is not None:
            raise error
        return next((fact for fact in self.facts if fact.identity == identity), None)

    def find_by_source_document(self, document_identity: Identifier) -> tuple[ValuationFact, ...]:
        return ()

    def find_by_source_movement(self, movement_identity: Identifier) -> tuple[ValuationFact, ...]:
        return ()

    def find_by_valuation_key(self, valuation_key: ValuationKey) -> tuple[ValuationFact, ...]:
        return ()

    def enumerate(self) -> tuple[ValuationFact, ...]:
        return tuple(self.facts)


def _service(
    operation: ValuationOperationRecord | None,
    facts: tuple[ValuationFact, ...] = (),
) -> tuple[DefaultValuationOperationRecoveryService, OperationPersistence, FactPersistence]:
    operations = OperationPersistence(operation)
    fact_persistence = FactPersistence(facts)
    fact_recovery = ValuationFactRecoveryService(fact_persistence=fact_persistence)
    service = DefaultValuationOperationRecoveryService(
        operation_persistence=operations,
        fact_persistence=fact_persistence,
        fact_recovery_service=fact_recovery,
        fact_identity_factory=DefaultValuationFactIdentityFactory(),
    )
    return service, operations, fact_persistence


def test_operation_recovery_fails_when_operation_is_missing() -> None:
    service, _, _ = _service(None)

    result = service.recover(ValuationOperationIdentity("remove-001"))

    assert result.outcome is ValuationRecoveryOutcome.FAILURE
    assert isinstance(result.error, ValuationNotFoundError)


def test_operation_recovery_fails_for_non_remove_operation() -> None:
    operation = ValuationOperationRecord(
        identity=ValuationOperationIdentity("establish-001"),
        operation_type=ValuationOperationType.ESTABLISH,
        document_identity=_id(),
        fingerprint="fingerprint",
    )
    service, _, _ = _service(operation)

    result = service.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.FAILURE


def test_operation_recovery_succeeds_for_empty_remove() -> None:
    operation = _operation(())
    service, _, facts = _service(operation)

    result = service.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.SUCCESS
    assert facts.append_calls == []


def test_operation_recovery_appends_missing_reversal() -> None:
    layer = _layer()
    operation = _operation((layer.identity,))
    service, _, facts = _service(operation, (layer,))

    result = service.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.SUCCESS
    assert len(facts.append_calls) == 1
    reversal = facts.append_calls[0][0]
    assert isinstance(reversal, ValuationReversal)
    assert reversal.reversed_identity == layer.identity
    assert reversal.operation_identity == operation.identity


def test_operation_recovery_is_idempotent() -> None:
    layer = _layer()
    operation = _operation((layer.identity,))
    service, _, facts = _service(operation, (layer,))

    first = service.recover(operation.identity)
    second = service.recover(operation.identity)

    assert first.outcome is ValuationRecoveryOutcome.SUCCESS
    assert second.outcome is ValuationRecoveryOutcome.SUCCESS
    assert len(facts.append_calls) == 1


def test_operation_recovery_fails_when_target_is_missing() -> None:
    target_id = _id()
    operation = _operation((target_id,))
    service, _, facts = _service(operation)

    result = service.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.FAILURE
    assert facts.append_calls == []


def test_operation_recovery_is_indeterminate_when_target_lookup_is_indeterminate() -> None:
    target_id = _id()
    layer = _layer(target_id)
    operation = _operation((target_id,))
    service, _, facts = _service(operation, (layer,))
    facts.find_errors[target_id] = PersistenceIndeterminateError("read failed")

    result = service.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.INDETERMINATE
    assert facts.append_calls == []


def test_operation_recovery_rejects_noncanonical_target_order() -> None:
    first = _layer()
    second = _layer()
    ordered = tuple(sorted((first.identity, second.identity), key=str))
    noncanonical = tuple(reversed(ordered))
    operation = _operation(noncanonical)
    service, _, _ = _service(operation, (first, second))

    result = service.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.FAILURE


def test_operation_recovery_rejects_duplicate_targets() -> None:
    layer = _layer()
    operation = _operation((layer.identity, layer.identity))
    service, _, _ = _service(operation, (layer,))

    result = service.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.FAILURE
