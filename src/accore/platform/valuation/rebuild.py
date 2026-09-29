from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Protocol

from accore.platform.foundation import Identifier
from accore.platform.persistence.errors import PersistenceError, PersistenceIndeterminateError

from .errors import ValuationConflictError, ValuationPersistenceError, ValuationValidationError

_ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _encode_ulid(value: bytes) -> str:
    if len(value) != 16:
        raise ValueError("ULID encoding requires exactly 16 bytes.")
    number = int.from_bytes(value, byteorder="big")
    characters = ["0"] * 26
    for index in range(25, -1, -1):
        characters[index] = _ULID_ALPHABET[number & 0x1F]
        number >>= 5
    return "".join(characters)


from .facts import (
    ValuationAdjustment,
    ValuationAllocation,
    ValuationConsumption,
    ValuationFact,
    ValuationLayer,
    ValuationReversal,
)
from .key import ValuationKey
from .persistence import ValuationFactPersistence, ValuationResultPersistence
from .results import CostMovement
from .totals import CostTotalsEngine


class ValuationCostMovementRole(StrEnum):
    ORIGINAL = "original"
    REVERSAL = "reversal"


def _canonical_identity_payload(fact: ValuationFact, role: ValuationCostMovementRole) -> str:
    payload = {
        "fact_identity": str(fact.identity),
        "movement_role": role.value,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


class ValuationCostMovementIdentityFactory(Protocol):
    def create(
        self,
        fact: ValuationFact,
        role: ValuationCostMovementRole,
    ) -> Identifier: ...


class DefaultValuationCostMovementIdentityFactory:
    def create(
        self,
        fact: ValuationFact,
        role: ValuationCostMovementRole,
    ) -> Identifier:
        digest = hashlib.sha256(_canonical_identity_payload(fact, role).encode("utf-8")).digest()
        return Identifier.from_str(_encode_ulid(digest[:16]))


class ValuationFactToCostMovementProjector(Protocol):
    def project(
        self,
        fact: ValuationFact,
        facts: ValuationFactPersistence,
    ) -> tuple[CostMovement, ...]: ...


class DefaultValuationFactToCostMovementProjector:
    def __init__(
        self,
        *,
        movement_identity_factory: ValuationCostMovementIdentityFactory | None = None,
    ) -> None:
        self._movement_identity_factory = (
            movement_identity_factory or DefaultValuationCostMovementIdentityFactory()
        )

    def project(
        self,
        fact: ValuationFact,
        facts: ValuationFactPersistence,
    ) -> tuple[CostMovement, ...]:
        if isinstance(fact, ValuationReversal):
            reversed_fact = facts.find(fact.reversed_identity)
            if reversed_fact is None:
                raise ValuationValidationError(
                    "Valuation reversal references a missing authoritative valuation fact."
                )
            if isinstance(reversed_fact, ValuationReversal):
                raise ValuationValidationError(
                    "Valuation reversal cannot reverse another valuation reversal."
                )
            original = self._project_original(reversed_fact, facts)
            return tuple(
                CostMovement(
                    identity=self._movement_identity_factory.create(
                        fact,
                        ValuationCostMovementRole.REVERSAL,
                    ),
                    valuation_key=fact.valuation_key,
                    quantity=-movement.quantity,
                    cost=-movement.cost,
                    source_identity=fact.source_identity,
                    created_at=fact.created_at,
                )
                for movement in original
            )

        return self._project_original(fact, facts)

    def _project_original(
        self,
        fact: ValuationFact,
        facts: ValuationFactPersistence,
    ) -> tuple[CostMovement, ...]:
        if isinstance(fact, ValuationLayer):
            return (
                self._movement(
                    fact=fact,
                    quantity=fact.quantity,
                    cost=fact.total_cost,
                    source_identity=fact.source_movement_identity,
                ),
            )

        if isinstance(fact, ValuationConsumption):
            return (
                self._movement(
                    fact=fact,
                    quantity=-fact.quantity,
                    cost=-fact.cost,
                    source_identity=fact.source_identity,
                ),
            )

        if isinstance(fact, ValuationAdjustment):
            # An adjustment becomes a valuation effect only when allocated.
            return ()

        if isinstance(fact, ValuationAllocation):
            return (
                self._movement(
                    fact=fact,
                    quantity=Decimal(0),
                    cost=fact.amount,
                    source_identity=fact.adjustment_identity,
                ),
            )

        raise TypeError(f"Unsupported valuation fact: {type(fact)!r}")

    def _movement(
        self,
        *,
        fact: ValuationFact,
        quantity: Decimal,
        cost: Decimal,
        source_identity: Identifier,
    ) -> CostMovement:
        return CostMovement(
            identity=self._movement_identity_factory.create(
                fact,
                ValuationCostMovementRole.ORIGINAL,
            ),
            valuation_key=fact.valuation_key,
            quantity=quantity,
            cost=cost,
            source_identity=source_identity,
            created_at=fact.created_at,
        )


class ValuationRebuildOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class ValuationRebuildResult:
    outcome: ValuationRebuildOutcome
    rebuilt_valuation_keys: tuple[ValuationKey, ...] = ()
    error: Exception | None = None


class DefaultValuationRebuilder:
    def __init__(
        self,
        *,
        fact_persistence: ValuationFactPersistence,
        result_persistence: ValuationResultPersistence,
        totals_engine: CostTotalsEngine,
        projector: ValuationFactToCostMovementProjector | None = None,
    ) -> None:
        self._fact_persistence = fact_persistence
        self._result_persistence = result_persistence
        self._totals_engine = totals_engine
        self._projector = projector or DefaultValuationFactToCostMovementProjector()

    def rebuild(self) -> ValuationRebuildResult:
        try:
            facts = tuple(self._fact_persistence.enumerate())
            expected = self._project(facts)
            self._reconcile_all(expected)
            keys = self._valuation_keys(facts, expected)
            keys.update(
                balance.valuation_key for balance in self._result_persistence.enumerate_balances()
            )
            self._rebuild_balances(tuple(sorted(keys, key=str)))
            return ValuationRebuildResult(
                ValuationRebuildOutcome.SUCCESS,
                tuple(sorted(keys, key=str)),
            )
        except ValuationConflictError as exc:
            return ValuationRebuildResult(ValuationRebuildOutcome.FAILURE, error=exc)
        except ValuationValidationError as exc:
            return ValuationRebuildResult(ValuationRebuildOutcome.FAILURE, error=exc)
        except ValuationPersistenceError as exc:
            outcome = (
                ValuationRebuildOutcome.FAILURE
                if exc.rollback_guaranteed
                else ValuationRebuildOutcome.INDETERMINATE
            )
            return ValuationRebuildResult(outcome, error=exc)
        except PersistenceIndeterminateError as exc:
            return ValuationRebuildResult(ValuationRebuildOutcome.INDETERMINATE, error=exc)
        except PersistenceError as exc:
            return ValuationRebuildResult(ValuationRebuildOutcome.INDETERMINATE, error=exc)

    def rebuild_for(self, valuation_key: ValuationKey) -> ValuationRebuildResult:
        try:
            facts = tuple(self._fact_persistence.find_by_valuation_key(valuation_key))
            expected = self._project(facts)
            existing = tuple(self._result_persistence.enumerate_movements())
            retained = tuple(
                movement for movement in existing if movement.valuation_key != valuation_key
            )
            self._reconcile_all(retained + expected)
            self._rebuild_balances((valuation_key,))
            return ValuationRebuildResult(
                ValuationRebuildOutcome.SUCCESS,
                (valuation_key,),
            )
        except ValuationConflictError as exc:
            return ValuationRebuildResult(ValuationRebuildOutcome.FAILURE, error=exc)
        except ValuationValidationError as exc:
            return ValuationRebuildResult(ValuationRebuildOutcome.FAILURE, error=exc)
        except ValuationPersistenceError as exc:
            outcome = (
                ValuationRebuildOutcome.FAILURE
                if exc.rollback_guaranteed
                else ValuationRebuildOutcome.INDETERMINATE
            )
            return ValuationRebuildResult(outcome, error=exc)
        except PersistenceIndeterminateError as exc:
            return ValuationRebuildResult(ValuationRebuildOutcome.INDETERMINATE, error=exc)
        except PersistenceError as exc:
            return ValuationRebuildResult(ValuationRebuildOutcome.INDETERMINATE, error=exc)

    def _project(self, facts: Sequence[ValuationFact]) -> tuple[CostMovement, ...]:
        movements: dict[Identifier, CostMovement] = {}
        for fact in facts:
            for movement in self._projector.project(fact, self._fact_persistence):
                existing = movements.get(movement.identity)
                if existing is not None and existing != movement:
                    raise ValuationConflictError(
                        "Valuation movement identity has conflicting semantics."
                    )
                movements[movement.identity] = movement
        return tuple(sorted(movements.values(), key=lambda movement: str(movement.identity)))

    def _reconcile_all(self, expected: Sequence[CostMovement]) -> None:
        canonical = tuple(sorted(expected, key=lambda movement: str(movement.identity)))
        self._result_persistence.reconcile_movements(canonical)

    def _rebuild_balances(self, valuation_keys: Sequence[ValuationKey]) -> None:
        for valuation_key in sorted(set(valuation_keys), key=str):
            movements = self._result_persistence.find_movements(valuation_key)
            self._totals_engine.rebuild(valuation_key, movements)
            balance = self._totals_engine.get(valuation_key)
            self._result_persistence.replace_balance(balance)

    @staticmethod
    def _valuation_keys(
        facts: Sequence[ValuationFact],
        movements: Sequence[CostMovement],
    ) -> set[ValuationKey]:
        return {fact.valuation_key for fact in facts} | {
            movement.valuation_key for movement in movements
        }


class ValuationRebuilder(Protocol):
    def rebuild(self) -> ValuationRebuildResult: ...

    def rebuild_for(self, valuation_key: ValuationKey) -> ValuationRebuildResult: ...
