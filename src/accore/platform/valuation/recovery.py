from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from accore.platform.foundation import Identifier
from accore.platform.persistence.errors import (
    PersistenceError,
    PersistenceIndeterminateError,
)

from .errors import (
    ValuationConflictError,
    ValuationNotFoundError,
    ValuationPersistenceError,
    ValuationValidationError,
)
from .fact_identity import DefaultValuationFactIdentityFactory
from .facts import (
    ValuationConsumption,
    ValuationFact,
    ValuationFactIdentityFactory,
    ValuationFactType,
    ValuationLayer,
    ValuationReversal,
)
from .operations import (
    ValuationOperationIdentity,
    ValuationOperationRecord,
    ValuationOperationType,
)
from .persistence import ValuationFactPersistence, ValuationOperationPersistence


class ValuationFactRecoveryOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class ValuationFactRecoveryResult:
    outcome: ValuationFactRecoveryOutcome
    error: Exception | None = None


class ValuationRecoveryOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class ValuationRecoveryResult:
    outcome: ValuationRecoveryOutcome
    error: Exception | None = None


class ValuationOperationRecoveryService(Protocol):
    def recover(
        self,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationRecoveryResult: ...


class DefaultValuationOperationRecoveryService:
    """Recover reversal facts for an already registered REMOVE operation."""

    def __init__(
        self,
        *,
        operation_persistence: ValuationOperationPersistence,
        fact_persistence: ValuationFactPersistence,
        fact_recovery_service: ValuationFactRecoveryService,
        fact_identity_factory: ValuationFactIdentityFactory | None = None,
    ) -> None:
        self._operation_persistence = operation_persistence
        self._fact_persistence = fact_persistence
        self._fact_recovery_service = fact_recovery_service
        self._fact_identity_factory = fact_identity_factory or DefaultValuationFactIdentityFactory()

    def recover(
        self,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationRecoveryResult:
        try:
            operation = self._operation_persistence.find(operation_identity)
        except PersistenceIndeterminateError as exc:
            return ValuationRecoveryResult(ValuationRecoveryOutcome.INDETERMINATE, exc)
        except PersistenceError as exc:
            return ValuationRecoveryResult(ValuationRecoveryOutcome.INDETERMINATE, exc)

        if operation is None:
            return ValuationRecoveryResult(
                ValuationRecoveryOutcome.FAILURE,
                ValuationNotFoundError("Valuation operation was not found."),
            )

        if operation.operation_type is not ValuationOperationType.REMOVE:
            return ValuationRecoveryResult(
                ValuationRecoveryOutcome.FAILURE,
                ValuationValidationError("Only REMOVE valuation operations are recoverable."),
            )

        target_ids = operation.target_fact_identities
        if len(target_ids) != len(set(target_ids)):
            return ValuationRecoveryResult(
                ValuationRecoveryOutcome.FAILURE,
                ValuationValidationError(
                    "REMOVE operation contains duplicate target valuation fact identities."
                ),
            )

        if target_ids != tuple(sorted(target_ids, key=str)):
            return ValuationRecoveryResult(
                ValuationRecoveryOutcome.FAILURE,
                ValuationValidationError(
                    "REMOVE operation target valuation fact identities are not canonical."
                ),
            )

        targets: list[ValuationFact] = []
        for target_id in target_ids:
            try:
                fact = self._fact_persistence.find(target_id)
            except PersistenceIndeterminateError as exc:
                return ValuationRecoveryResult(ValuationRecoveryOutcome.INDETERMINATE, exc)
            except PersistenceError as exc:
                return ValuationRecoveryResult(ValuationRecoveryOutcome.INDETERMINATE, exc)

            if fact is None:
                return ValuationRecoveryResult(
                    ValuationRecoveryOutcome.FAILURE,
                    ValuationNotFoundError(
                        "Registered REMOVE target valuation fact was not found."
                    ),
                )

            if not isinstance(fact, (ValuationLayer, ValuationConsumption)):
                return ValuationRecoveryResult(
                    ValuationRecoveryOutcome.FAILURE,
                    ValuationValidationError(
                        "Registered REMOVE target is not a reversible valuation fact."
                    ),
                )

            targets.append(fact)

        reversal_facts = self._build_reversal_facts(operation, tuple(targets))
        recovery = self._fact_recovery_service.reconcile(operation, reversal_facts)

        return ValuationRecoveryResult(
            ValuationRecoveryOutcome(recovery.outcome.value),
            recovery.error,
        )

    def _build_reversal_facts(
        self,
        operation: ValuationOperationRecord,
        originals: tuple[ValuationFact, ...],
    ) -> tuple[ValuationReversal, ...]:
        reversals: list[ValuationReversal] = []
        for fact in originals:
            if isinstance(fact, ValuationLayer):
                source_identity = fact.source_movement_identity
            elif isinstance(fact, ValuationConsumption):
                source_identity = fact.source_identity
            else:
                raise TypeError("Unsupported REMOVE target type.")

            identity = self._fact_identity_factory.for_operation_fact(
                operation.identity,
                ValuationFactType.REVERSAL,
                (
                    fact.identity,
                    fact.valuation_key,
                    operation.document_identity,
                    source_identity,
                    fact.created_at,
                ),
            )
            reversals.append(
                ValuationReversal(
                    identity=identity,
                    operation_identity=operation.identity,
                    reversed_identity=fact.identity,
                    valuation_key=fact.valuation_key,
                    document_identity=operation.document_identity,
                    source_identity=source_identity,
                    created_at=fact.created_at,
                )
            )

        return tuple(reversals)


class ValuationFactRecoveryService:
    """Reconcile deterministic valuation facts against authoritative persistence."""

    def __init__(self, *, fact_persistence: ValuationFactPersistence) -> None:
        self._fact_persistence = fact_persistence

    def reconcile(
        self,
        operation: ValuationOperationRecord,
        expected_facts: Sequence[ValuationFact],
    ) -> ValuationFactRecoveryResult:
        del operation  # Expected deterministic facts carry the operation identity.

        expected = tuple(expected_facts)

        try:
            missing = self._find_missing(expected)
        except ValuationConflictError as exc:
            return ValuationFactRecoveryResult(
                ValuationFactRecoveryOutcome.FAILURE,
                exc,
            )
        except PersistenceIndeterminateError as exc:
            return ValuationFactRecoveryResult(
                ValuationFactRecoveryOutcome.INDETERMINATE,
                exc,
            )
        except PersistenceError as exc:
            return ValuationFactRecoveryResult(
                ValuationFactRecoveryOutcome.INDETERMINATE,
                exc,
            )

        if not missing:
            return ValuationFactRecoveryResult(ValuationFactRecoveryOutcome.SUCCESS)

        return self._append_and_reconcile(missing)

    def _find_missing(
        self,
        expected: Sequence[ValuationFact],
    ) -> tuple[ValuationFact, ...]:
        missing: list[ValuationFact] = []
        seen: dict[Identifier, ValuationFact] = {}

        for fact in expected:
            previous = seen.get(fact.identity)

            if previous is not None:
                if previous != fact:
                    raise ValuationConflictError(
                        "Expected valuation facts contain the same identity "
                        "with different semantics."
                    )
                continue

            seen[fact.identity] = fact

            existing = self._fact_persistence.find(fact.identity)
            if existing is None:
                missing.append(fact)
            elif existing != fact:
                raise ValuationConflictError(
                    "Valuation fact identity already exists with different semantics."
                )

        return tuple(missing)

    def _append_and_reconcile(
        self,
        missing: tuple[ValuationFact, ...],
    ) -> ValuationFactRecoveryResult:
        current_missing = missing
        last_error: Exception | None = None

        for attempt in range(2):
            try:
                self._fact_persistence.append(current_missing)
            except ValuationConflictError as exc:
                return ValuationFactRecoveryResult(
                    ValuationFactRecoveryOutcome.FAILURE,
                    exc,
                )
            except ValuationPersistenceError as exc:
                if exc.rollback_guaranteed:
                    return ValuationFactRecoveryResult(
                        ValuationFactRecoveryOutcome.FAILURE,
                        exc,
                    )
                last_error = exc
            except PersistenceIndeterminateError as exc:
                last_error = exc
            except PersistenceError as exc:
                last_error = exc
            else:
                return ValuationFactRecoveryResult(ValuationFactRecoveryOutcome.SUCCESS)

            try:
                current_missing = self._find_missing(current_missing)
            except ValuationConflictError as exc:
                return ValuationFactRecoveryResult(
                    ValuationFactRecoveryOutcome.FAILURE,
                    exc,
                )
            except PersistenceIndeterminateError as exc:
                return ValuationFactRecoveryResult(
                    ValuationFactRecoveryOutcome.INDETERMINATE,
                    exc,
                )
            except PersistenceError as exc:
                return ValuationFactRecoveryResult(
                    ValuationFactRecoveryOutcome.INDETERMINATE,
                    exc,
                )

            if not current_missing:
                return ValuationFactRecoveryResult(ValuationFactRecoveryOutcome.SUCCESS)

            if attempt == 1:
                return ValuationFactRecoveryResult(
                    ValuationFactRecoveryOutcome.INDETERMINATE,
                    last_error,
                )

        return ValuationFactRecoveryResult(
            ValuationFactRecoveryOutcome.INDETERMINATE,
            last_error,
        )


__all__ = [
    "DefaultValuationOperationRecoveryService",
    "ValuationFactRecoveryOutcome",
    "ValuationFactRecoveryResult",
    "ValuationFactRecoveryService",
    "ValuationOperationRecoveryService",
    "ValuationRecoveryOutcome",
    "ValuationRecoveryResult",
]
