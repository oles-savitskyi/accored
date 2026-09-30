from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.persistence import PersistenceIndeterminateError
from accore.platform.valuation import (
    DefaultValuationFactIdentityFactory,
    DefaultValuationOperationRecoveryService,
    LayerEstablishmentPlan,
    PlannedLayerReference,
    ValuationEstablishRecoveryDescriptor,
    ValuationFact,
    ValuationFactRecoveryService,
    ValuationKey,
    ValuationLayer,
    ValuationNotFoundError,
    ValuationOperationIdentity,
    ValuationOperationRecord,
    ValuationOperationType,
    ValuationRebuildOutcome,
    ValuationRebuildResult,
    ValuationRecoveryOutcome,
    ValuationReversal,
)

KEY = ValuationKey({"product": "PR-01"})
WHEN = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)


class FakeRebuilder:
    def __init__(self, result: ValuationRebuildResult | None = None) -> None:
        self.result = result or ValuationRebuildResult(ValuationRebuildOutcome.SUCCESS)
        self.calls = 0

    def rebuild(self) -> ValuationRebuildResult:
        self.calls += 1
        return self.result

    def rebuild_for(self, valuation_key: ValuationKey) -> ValuationRebuildResult:
        del valuation_key
        return self.result


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


def _establish_descriptor(document_identity: Identifier) -> ValuationEstablishRecoveryDescriptor:
    return ValuationEstablishRecoveryDescriptor(
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
    rebuilder: FakeRebuilder | None = None,
) -> tuple[
    DefaultValuationOperationRecoveryService, OperationPersistence, FactPersistence, FakeRebuilder
]:
    operations = OperationPersistence(operation)
    fact_persistence = FactPersistence(facts)
    fact_recovery = ValuationFactRecoveryService(fact_persistence=fact_persistence)
    actual_rebuilder = rebuilder or FakeRebuilder()
    service = DefaultValuationOperationRecoveryService(
        operation_persistence=operations,
        fact_persistence=fact_persistence,
        fact_recovery_service=fact_recovery,
        fact_identity_factory=DefaultValuationFactIdentityFactory(),
        rebuilder=actual_rebuilder,
    )
    return service, operations, fact_persistence, actual_rebuilder


def test_operation_recovery_fails_when_operation_is_missing() -> None:
    service, _, _, _ = _service(None)

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
    service, _, _, _ = _service(operation)

    result = service.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.FAILURE


def test_operation_recovery_succeeds_for_empty_remove() -> None:
    operation = _operation(())
    service, _, facts, _ = _service(operation)

    result = service.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.SUCCESS
    assert facts.append_calls == []


def test_operation_recovery_appends_missing_reversal() -> None:
    layer = _layer()
    operation = _operation((layer.identity,))
    service, _, facts, _ = _service(operation, (layer,))

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
    service, _, facts, _ = _service(operation, (layer,))

    first = service.recover(operation.identity)
    second = service.recover(operation.identity)

    assert first.outcome is ValuationRecoveryOutcome.SUCCESS
    assert second.outcome is ValuationRecoveryOutcome.SUCCESS
    assert len(facts.append_calls) == 1


def test_operation_recovery_fails_when_target_is_missing() -> None:
    target_id = _id()
    operation = _operation((target_id,))
    service, _, facts, _ = _service(operation)

    result = service.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.FAILURE
    assert facts.append_calls == []


def test_operation_recovery_is_indeterminate_when_target_lookup_is_indeterminate() -> None:
    target_id = _id()
    layer = _layer(target_id)
    operation = _operation((target_id,))
    service, _, facts, _ = _service(operation, (layer,))
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
    service, _, _, _ = _service(operation, (first, second))

    result = service.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.FAILURE


def test_operation_recovery_rejects_duplicate_targets() -> None:
    layer = _layer()
    operation = _operation((layer.identity, layer.identity))
    service, _, _, _ = _service(operation, (layer,))

    result = service.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.FAILURE


def test_establish_recovery_reconstructs_and_persists_missing_facts() -> None:
    document_identity = _id()
    descriptor = _establish_descriptor(document_identity)
    operation = ValuationOperationRecord(
        identity=ValuationOperationIdentity("establish-001"),
        operation_type=ValuationOperationType.ESTABLISH,
        document_identity=document_identity,
        fingerprint="fingerprint",
        establish_descriptor=descriptor,
    )
    service, operations, facts, _ = _service(operation)

    result = service.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.SUCCESS
    assert len(facts.facts) == 1
    assert facts.facts[0].operation_identity == operation.identity
    assert operations.operation == operation


def test_establish_recovery_is_idempotent_when_facts_already_exist() -> None:
    document_identity = _id()
    descriptor = _establish_descriptor(document_identity)
    operation = ValuationOperationRecord(
        identity=ValuationOperationIdentity("establish-001"),
        operation_type=ValuationOperationType.ESTABLISH,
        document_identity=document_identity,
        fingerprint="fingerprint",
        establish_descriptor=descriptor,
    )
    service, _, facts, _ = _service(operation)

    first = service.recover(operation.identity)
    append_calls = len(facts.append_calls)
    second = service.recover(operation.identity)

    assert first.outcome is ValuationRecoveryOutcome.SUCCESS
    assert second.outcome is ValuationRecoveryOutcome.SUCCESS
    assert len(facts.append_calls) == append_calls


def test_establish_recovery_fails_when_descriptor_is_missing() -> None:
    operation = ValuationOperationRecord(
        identity=ValuationOperationIdentity("establish-001"),
        operation_type=ValuationOperationType.ESTABLISH,
        document_identity=_id(),
        fingerprint="fingerprint",
    )
    service, _, _, _ = _service(operation)

    result = service.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.FAILURE


def test_establish_recovery_does_not_create_another_operation_record() -> None:
    document_identity = _id()
    operation = ValuationOperationRecord(
        identity=ValuationOperationIdentity("establish-001"),
        operation_type=ValuationOperationType.ESTABLISH,
        document_identity=document_identity,
        fingerprint="fingerprint",
        establish_descriptor=_establish_descriptor(document_identity),
    )
    service, operations, _, _ = _service(operation)

    service.recover(operation.identity)

    assert operations.find_calls == [operation.identity]
    assert operations.operation == operation


def test_operation_recovery_rebuilds_derived_state_after_fact_recovery() -> None:
    layer = _layer()
    operation = _operation((layer.identity,))
    rebuilder = FakeRebuilder()
    service, _, _, actual_rebuilder = _service(operation, (layer,), rebuilder)

    result = service.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.SUCCESS
    assert actual_rebuilder.calls == 1


def test_operation_recovery_does_not_rebuild_when_fact_recovery_fails() -> None:
    operation = _operation((_id(),))
    rebuilder = FakeRebuilder()
    service, _, facts, actual_rebuilder = _service(operation, (), rebuilder)

    result = service.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.FAILURE
    assert facts.append_calls == []
    assert actual_rebuilder.calls == 0


def test_operation_recovery_propagates_derived_failure() -> None:
    operation = _operation(())
    error = RuntimeError("rebuild failed")
    rebuilder = FakeRebuilder(ValuationRebuildResult(ValuationRebuildOutcome.FAILURE, error=error))
    service, _, _, actual_rebuilder = _service(operation, (), rebuilder)

    result = service.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.FAILURE
    assert result.error is error
    assert actual_rebuilder.calls == 1


def test_operation_recovery_propagates_derived_indeterminate() -> None:
    operation = _operation(())
    error = PersistenceIndeterminateError("rebuild uncertain")
    rebuilder = FakeRebuilder(
        ValuationRebuildResult(ValuationRebuildOutcome.INDETERMINATE, error=error)
    )
    service, _, _, actual_rebuilder = _service(operation, (), rebuilder)

    result = service.recover(operation.identity)

    assert result.outcome is ValuationRecoveryOutcome.INDETERMINATE
    assert result.error is error
    assert actual_rebuilder.calls == 1
