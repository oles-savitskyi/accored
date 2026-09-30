from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum, StrEnum
from typing import Protocol

from accore.platform.foundation import Identifier
from accore.platform.persistence.errors import (
    PersistenceError,
    PersistenceIndeterminateError,
)

from .errors import (
    ValuationConflictError,
    ValuationPersistenceError,
    ValuationValidationError,
)
from .fact_builder import DefaultValuationFactBuilder, ValuationFactBuilder
from .fact_identity import DefaultValuationFactIdentityFactory
from .facts import (
    ValuationConsumption,
    ValuationFact,
    ValuationFactIdentityFactory,
    ValuationFactType,
    ValuationLayer,
    ValuationReversal,
)
from .key import ValuationKey
from .operations import (
    ValuationEstablishRecoveryDescriptor,
    ValuationOperationIdentity,
    ValuationOperationRecord,
    ValuationOperationType,
)
from .persistence import (
    ValuationFactPersistence,
    ValuationOperationPersistence,
    ValuationResultPersistence,
)
from .plan import (
    ConsumptionPlan,
    LayerEstablishmentPlan,
    ValuationPlan,
)
from .rebuild import (
    DefaultValuationCostMovementIdentityFactory,
    ValuationCostMovementIdentityFactory,
    ValuationCostMovementRole,
    ValuationRebuilder,
)
from .recovery import (
    DefaultValuationOperationRecoveryService,
    ValuationFactRecoveryOutcome,
    ValuationFactRecoveryService,
    ValuationRecoveryResult,
)
from .results import CostBalance, CostMovement
from .totals import CostTotalsEngine
from .validation import ValuationPlanValidator


def _canonicalize(value: object) -> object:
    if isinstance(value, Identifier):
        return {
            "__type__": "Identifier",
            "value": str(value),
        }

    if isinstance(value, Decimal):
        return {
            "__type__": "Decimal",
            "value": str(value),
        }

    if isinstance(value, (datetime, date)):
        return {
            "__type__": type(value).__qualname__,
            "value": value.isoformat(),
        }

    if isinstance(value, Enum):
        return {
            "__type__": type(value).__qualname__,
            "value": value.value,
        }

    if is_dataclass(value):
        return {
            "__type__": type(value).__qualname__,
            **{field.name: _canonicalize(getattr(value, field.name)) for field in fields(value)},
        }

    if isinstance(value, tuple):
        return [_canonicalize(item) for item in value]

    if isinstance(value, list):
        return [_canonicalize(item) for item in value]

    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }

    if value is None or isinstance(value, (bool, int, float, str)):
        return value

    raise TypeError(f"Unsupported value for valuation operation fingerprint: {type(value)!r}")


def _fingerprint(payload: object) -> str:
    serialized = json.dumps(
        _canonicalize(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _establish_fingerprint(plan: ValuationPlan) -> str:
    return _fingerprint(
        {
            "operation_type": ValuationOperationType.ESTABLISH.value,
            "plan": plan,
        }
    )


def _canonical_remove_target_identities(
    target_identities: tuple[Identifier, ...],
) -> tuple[Identifier, ...]:
    if len(target_identities) != len(set(target_identities)):
        raise ValuationValidationError(
            "REMOVE target selection contains duplicate valuation fact identities."
        )

    return tuple(sorted(target_identities, key=str))


def _remove_fingerprint(
    document_identity: Identifier,
    target_identities: tuple[Identifier, ...],
) -> str:
    return _fingerprint(
        {
            "operation_type": ValuationOperationType.REMOVE.value,
            "document_identity": document_identity,
            "target_identities": target_identities,
        }
    )


class ValuationEstablishPreparationOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class ValuationEstablishPreparationResult:
    outcome: ValuationEstablishPreparationOutcome
    error: Exception | None = None


class ValuationEstablishmentOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class ValuationEstablishmentResult:
    outcome: ValuationEstablishmentOutcome
    error: Exception | None = None


class ValuationRemovalOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class ValuationRemovalResult:
    outcome: ValuationRemovalOutcome
    error: Exception | None = None


class ValuationLifecycleCoordinator(Protocol):
    def prepare_establish(
        self,
        plan: ValuationPlan,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationEstablishPreparationResult: ...

    def establish(
        self,
        plan: ValuationPlan,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationEstablishmentResult: ...

    def remove(
        self,
        document_identity: Identifier,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationRemovalResult: ...

    def recover(
        self,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationRecoveryResult: ...


ValuationCoordinator = ValuationLifecycleCoordinator


class DefaultValuationCoordinator:
    """Orchestrate valuation establishment without owning physical transactions."""

    def __init__(
        self,
        *,
        fact_persistence: ValuationFactPersistence,
        operation_persistence: ValuationOperationPersistence,
        result_persistence: ValuationResultPersistence,
        totals_engine: CostTotalsEngine,
        validator: ValuationPlanValidator,
        fact_identity_factory: ValuationFactIdentityFactory | None = None,
        fact_recovery_service: ValuationFactRecoveryService | None = None,
        rebuilder: ValuationRebuilder,
        movement_identity_factory: ValuationCostMovementIdentityFactory | None = None,
    ) -> None:
        self._fact_persistence = fact_persistence
        self._operation_persistence = operation_persistence
        self._result_persistence = result_persistence
        self._totals_engine = totals_engine
        self._validator = validator
        self._fact_identity_factory = fact_identity_factory or DefaultValuationFactIdentityFactory()
        self._fact_builder: ValuationFactBuilder = DefaultValuationFactBuilder(
            fact_identity_factory=self._fact_identity_factory
        )
        self._movement_identity_factory = (
            movement_identity_factory or DefaultValuationCostMovementIdentityFactory()
        )
        self._fact_recovery_service = fact_recovery_service or ValuationFactRecoveryService(
            fact_persistence=fact_persistence
        )
        self._operation_recovery_service = DefaultValuationOperationRecoveryService(
            operation_persistence=operation_persistence,
            fact_persistence=fact_persistence,
            fact_recovery_service=self._fact_recovery_service,
            fact_identity_factory=self._fact_identity_factory,
            fact_builder=self._fact_builder,
            rebuilder=rebuilder,
        )

    def _register_operation(
        self,
        operation: ValuationOperationRecord,
    ) -> tuple[ValuationEstablishmentOutcome, Exception | None]:
        try:
            self._operation_persistence.append(operation)
            return ValuationEstablishmentOutcome.SUCCESS, None

        except ValuationConflictError as exc:
            return ValuationEstablishmentOutcome.FAILURE, exc

        except PersistenceIndeterminateError:
            try:
                existing = self._operation_persistence.find(operation.identity)
            except PersistenceIndeterminateError as find_exc:
                return ValuationEstablishmentOutcome.INDETERMINATE, find_exc
            except PersistenceError as find_exc:
                return ValuationEstablishmentOutcome.INDETERMINATE, find_exc

            if existing is not None:
                if existing != operation:
                    return (
                        ValuationEstablishmentOutcome.FAILURE,
                        ValuationConflictError(
                            "Valuation operation identity already exists with different semantics."
                        ),
                    )

                return ValuationEstablishmentOutcome.SUCCESS, None

            try:
                self._operation_persistence.append(operation)
            except ValuationConflictError as retry_exc:
                return ValuationEstablishmentOutcome.FAILURE, retry_exc
            except PersistenceIndeterminateError as retry_exc:
                return ValuationEstablishmentOutcome.INDETERMINATE, retry_exc
            except ValuationPersistenceError as retry_exc:
                outcome = (
                    ValuationEstablishmentOutcome.FAILURE
                    if retry_exc.rollback_guaranteed
                    else ValuationEstablishmentOutcome.INDETERMINATE
                )
                return outcome, retry_exc
            except PersistenceError as retry_exc:
                return ValuationEstablishmentOutcome.INDETERMINATE, retry_exc

            return ValuationEstablishmentOutcome.SUCCESS, None

        except ValuationPersistenceError as exc:
            outcome = (
                ValuationEstablishmentOutcome.FAILURE
                if exc.rollback_guaranteed
                else ValuationEstablishmentOutcome.INDETERMINATE
            )
            return outcome, exc

        except PersistenceError as exc:
            return ValuationEstablishmentOutcome.INDETERMINATE, exc

    def _build_establish_operation(
        self,
        plan: ValuationPlan,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationOperationRecord:
        self._validator.validate(plan)
        document_identity = self._establish_document_identity(plan)
        descriptor = ValuationEstablishRecoveryDescriptor(
            document_identity=document_identity,
            operations=plan.operations,
        )
        return ValuationOperationRecord(
            identity=operation_identity,
            operation_type=ValuationOperationType.ESTABLISH,
            document_identity=document_identity,
            fingerprint=_establish_fingerprint(plan),
            establish_descriptor=descriptor,
        )

    def prepare_establish(
        self,
        plan: ValuationPlan,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationEstablishPreparationResult:
        try:
            operation = self._build_establish_operation(plan, operation_identity)
        except ValuationValidationError as exc:
            return ValuationEstablishPreparationResult(
                ValuationEstablishPreparationOutcome.FAILURE,
                exc,
            )

        outcome, error = self._register_operation(operation)
        return ValuationEstablishPreparationResult(
            ValuationEstablishPreparationOutcome(outcome.value),
            error,
        )

    def establish(
        self,
        plan: ValuationPlan,
        operation_identity: ValuationOperationIdentity | None = None,
    ) -> ValuationEstablishmentResult:
        effective_operation_identity = operation_identity or ValuationOperationIdentity(
            str(Identifier.new())
        )
        try:
            operation = self._build_establish_operation(plan, effective_operation_identity)
        except ValuationValidationError as exc:
            return ValuationEstablishmentResult(
                ValuationEstablishmentOutcome.FAILURE,
                exc,
            )

        outcome, error = self._register_operation(operation)
        if outcome is not ValuationEstablishmentOutcome.SUCCESS:
            return ValuationEstablishmentResult(outcome, error)

        try:
            facts = self._fact_builder.build(plan, operation.identity)
            movements = self._build_original_movements(facts)
            self._append_or_recover_facts(operation, facts)
            self._result_persistence.append_movements(movements)

            balances: dict[ValuationKey, CostBalance] = {}
            for movement in movements:
                balances[movement.valuation_key] = self._totals_engine.apply(movement)

            for balance in balances.values():
                self._result_persistence.replace_balance(balance)

        except ValuationPersistenceError as exc:
            outcome = (
                ValuationEstablishmentOutcome.FAILURE
                if exc.rollback_guaranteed
                else ValuationEstablishmentOutcome.INDETERMINATE
            )
            return ValuationEstablishmentResult(outcome, exc)
        except PersistenceIndeterminateError as exc:
            return ValuationEstablishmentResult(
                ValuationEstablishmentOutcome.INDETERMINATE,
                exc,
            )
        except PersistenceError as exc:
            return ValuationEstablishmentResult(
                ValuationEstablishmentOutcome.INDETERMINATE,
                exc,
            )

        return ValuationEstablishmentResult(ValuationEstablishmentOutcome.SUCCESS)

    @staticmethod
    def _establish_document_identity(plan: ValuationPlan) -> Identifier:
        document_identities: set[Identifier] = set()

        for operation in plan.operations:
            if isinstance(operation, LayerEstablishmentPlan):
                document_identities.add(operation.source_document_identity)
            elif isinstance(operation, ConsumptionPlan):
                document_identities.add(operation.document_identity)
            else:
                raise TypeError("ValuationPlan contains an unsupported operation.")

        if len(document_identities) != 1:
            raise ValuationValidationError(
                "ValuationPlan must contain exactly one document identity."
            )

        return next(iter(document_identities))

    def remove(
        self,
        document_identity: Identifier,
        operation_identity: ValuationOperationIdentity | None = None,
    ) -> ValuationRemovalResult:
        all_facts = tuple(self._fact_persistence.enumerate())

        try:
            targets = self._select_removal_targets(
                document_identity=document_identity,
                all_facts=all_facts,
            )
            active_consumptions = tuple(
                fact
                for fact in all_facts
                if isinstance(fact, ValuationConsumption)
                and fact.identity
                not in {
                    reversal.reversed_identity
                    for reversal in all_facts
                    if isinstance(reversal, ValuationReversal)
                }
            )
            self._validate_removal(
                document_identity=document_identity,
                originals=targets,
                active_consumptions=active_consumptions,
            )
        except ValuationValidationError as exc:
            return ValuationRemovalResult(ValuationRemovalOutcome.FAILURE, exc)

        canonical_target_identities = _canonical_remove_target_identities(
            tuple(fact.identity for fact in targets)
        )
        operation = ValuationOperationRecord(
            identity=operation_identity or ValuationOperationIdentity(str(Identifier.new())),
            operation_type=ValuationOperationType.REMOVE,
            document_identity=document_identity,
            fingerprint=_remove_fingerprint(
                document_identity=document_identity,
                target_identities=canonical_target_identities,
            ),
            target_fact_identities=canonical_target_identities,
        )

        operation_outcome, operation_error = self._register_operation(operation)

        if operation_outcome is ValuationEstablishmentOutcome.FAILURE:
            return ValuationRemovalResult(
                ValuationRemovalOutcome.FAILURE,
                operation_error,
            )

        if operation_outcome is ValuationEstablishmentOutcome.INDETERMINATE:
            return ValuationRemovalResult(
                ValuationRemovalOutcome.INDETERMINATE,
                operation_error,
            )

        if not targets:
            return ValuationRemovalResult(ValuationRemovalOutcome.SUCCESS)

        try:
            reversal_facts, movements = self._build_reversals(
                operation_identity=operation.identity,
                document_identity=document_identity,
                originals=targets,
            )

            self._append_or_recover_facts(operation, reversal_facts)
            self._result_persistence.append_movements(movements)
            self._rebuild_derived_state(movements)

        except ValuationValidationError as exc:
            return ValuationRemovalResult(
                ValuationRemovalOutcome.FAILURE,
                exc,
            )
        except ValuationConflictError as exc:
            return ValuationRemovalResult(
                ValuationRemovalOutcome.FAILURE,
                exc,
            )
        except ValuationPersistenceError as exc:
            removal_outcome = (
                ValuationRemovalOutcome.FAILURE
                if exc.rollback_guaranteed
                else ValuationRemovalOutcome.INDETERMINATE
            )
            return ValuationRemovalResult(removal_outcome, exc)
        except PersistenceIndeterminateError as exc:
            return ValuationRemovalResult(
                ValuationRemovalOutcome.INDETERMINATE,
                exc,
            )
        except PersistenceError as exc:
            return ValuationRemovalResult(
                ValuationRemovalOutcome.FAILURE,
                exc,
            )

        return ValuationRemovalResult(ValuationRemovalOutcome.SUCCESS)

    def recover(
        self,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationRecoveryResult:
        return self._operation_recovery_service.recover(operation_identity)

    def _append_or_recover_facts(
        self,
        operation: ValuationOperationRecord,
        facts: tuple[ValuationFact, ...],
    ) -> None:
        try:
            self._fact_persistence.append(facts)
            return
        except ValuationConflictError:
            raise
        except ValuationPersistenceError as exc:
            if exc.rollback_guaranteed:
                raise
        except PersistenceIndeterminateError:
            pass
        except PersistenceError:
            pass

        recovery = self._fact_recovery_service.reconcile(operation, facts)
        if recovery.outcome is ValuationFactRecoveryOutcome.SUCCESS:
            return
        if recovery.outcome is ValuationFactRecoveryOutcome.FAILURE:
            if recovery.error is not None:
                raise recovery.error
            raise ValuationConflictError("Valuation fact recovery failed.")
        if recovery.error is not None:
            raise PersistenceIndeterminateError(str(recovery.error))
        raise PersistenceIndeterminateError("Valuation fact recovery remains indeterminate.")

    @staticmethod
    def _select_removal_targets(
        *,
        document_identity: Identifier,
        all_facts: tuple[ValuationFact, ...],
    ) -> tuple[ValuationFact, ...]:
        reversed_ids = {
            reversal.reversed_identity
            for reversal in all_facts
            if isinstance(reversal, ValuationReversal)
        }

        candidates = tuple(
            fact
            for fact in all_facts
            if not isinstance(fact, ValuationReversal)
            and fact.identity not in reversed_ids
            and (
                (
                    isinstance(fact, ValuationLayer)
                    and fact.source_document_identity == document_identity
                )
                or (
                    isinstance(fact, ValuationConsumption)
                    and fact.document_identity == document_identity
                )
            )
        )

        target_identities = tuple(fact.identity for fact in candidates)
        canonical_identities = _canonical_remove_target_identities(target_identities)
        by_identity = {fact.identity: fact for fact in candidates}
        return tuple(by_identity[identity] for identity in canonical_identities)

    def _validate_removal(
        self,
        *,
        document_identity: Identifier,
        originals: tuple[ValuationFact, ...],
        active_consumptions: tuple[ValuationConsumption, ...],
    ) -> None:
        removed_consumption_ids = {
            fact.identity for fact in originals if isinstance(fact, ValuationConsumption)
        }

        for fact in originals:
            if isinstance(fact, ValuationLayer) and any(
                consumption.layer_identity == fact.identity
                and consumption.identity not in removed_consumption_ids
                and consumption.document_identity != document_identity
                for consumption in active_consumptions
            ):
                raise ValuationValidationError(
                    "Valuation layer cannot be reversed while another document consumes it."
                )

    def _build_reversals(
        self,
        *,
        operation_identity: ValuationOperationIdentity,
        document_identity: Identifier,
        originals: tuple[ValuationFact, ...],
    ) -> tuple[tuple[ValuationFact, ...], tuple[CostMovement, ...]]:
        reversal_facts: list[ValuationFact] = []
        movements: list[CostMovement] = []

        for fact in originals:
            if isinstance(fact, ValuationLayer):
                source_identity = fact.source_movement_identity
                quantity = -fact.quantity
                cost = -fact.total_cost
            elif isinstance(fact, ValuationConsumption):
                source_identity = fact.source_identity
                quantity = fact.quantity
                cost = fact.cost
            else:
                continue

            reversal = ValuationReversal(
                identity=self._fact_identity_factory.for_operation_fact(
                    operation_identity,
                    ValuationFactType.REVERSAL,
                    (
                        fact.identity,
                        fact.valuation_key,
                        document_identity,
                        source_identity,
                        fact.created_at,
                    ),
                ),
                operation_identity=operation_identity,
                reversed_identity=fact.identity,
                valuation_key=fact.valuation_key,
                document_identity=document_identity,
                source_identity=source_identity,
                created_at=fact.created_at,
            )
            reversal_facts.append(reversal)
            movements.append(
                CostMovement(
                    identity=self._movement_identity_factory.create(
                        reversal, ValuationCostMovementRole.REVERSAL
                    ),
                    valuation_key=fact.valuation_key,
                    quantity=quantity,
                    cost=cost,
                    source_identity=source_identity,
                    created_at=fact.created_at,
                )
            )

        return tuple(reversal_facts), tuple(movements)

    def _rebuild_derived_state(
        self,
        movements: tuple[CostMovement, ...],
    ) -> None:
        balances: dict[ValuationKey, CostBalance] = {}

        for movement in movements:
            balances[movement.valuation_key] = self._totals_engine.apply(movement)

        for balance in balances.values():
            self._result_persistence.replace_balance(balance)

    def _build_original_movements(
        self,
        facts: tuple[ValuationFact, ...],
    ) -> tuple[CostMovement, ...]:
        movements: list[CostMovement] = []

        for fact in facts:
            if isinstance(fact, ValuationLayer):
                movements.append(
                    CostMovement(
                        identity=self._movement_identity_factory.create(
                            fact, ValuationCostMovementRole.ORIGINAL
                        ),
                        valuation_key=fact.valuation_key,
                        quantity=fact.quantity,
                        cost=fact.total_cost,
                        source_identity=fact.source_movement_identity,
                        created_at=fact.created_at,
                    )
                )
                continue

            if isinstance(fact, ValuationConsumption):
                movements.append(
                    CostMovement(
                        identity=self._movement_identity_factory.create(
                            fact, ValuationCostMovementRole.ORIGINAL
                        ),
                        valuation_key=fact.valuation_key,
                        quantity=-fact.quantity,
                        cost=-fact.cost,
                        source_identity=fact.source_identity,
                        created_at=fact.created_at,
                    )
                )
                continue

            raise TypeError("Unsupported valuation fact type for original movement construction.")

        return tuple(movements)
