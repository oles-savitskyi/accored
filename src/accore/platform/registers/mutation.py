from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from accore.platform.foundation import Identifier

from .maintenance import (
    MaintenanceResult,
    TotalsMaintenanceCoordinator,
)
from .movement import Movement
from .operation_domain import RegisterOperationDomainRegistry
from .validation import MovementSetLike, MovementValidator

if TYPE_CHECKING:
    from accore.platform.persistence.facts import RegisterFactPersistence


class _MovementSet:
    """Internal adapter exposing a batch of Movements to the validator contract."""

    def __init__(self, movements: tuple[Movement, ...]) -> None:
        self.movements = movements


class RegisterMutationMaintenanceError(RuntimeError):
    """Raised when persisted Movement mutation cannot be reflected in Totals."""

    def __init__(
        self,
        register_identity: Identifier,
        result: MaintenanceResult,
    ) -> None:
        self.register_identity = register_identity
        self.result = result

        super().__init__(
            "Register mutation completed its authoritative persistence step, "
            "but Totals maintenance did not succeed: "
            f"register={register_identity!r}, "
            f"operation={result.operation.value!r}, "
            f"outcome={result.outcome.value!r}, "
            f"lifecycle={result.state.lifecycle.value!r}, "
            f"consistency={result.state.consistency.value!r}"
        )


class RegisterMutationOrchestrator:
    """Coordinate authoritative Movement mutation and derived Totals maintenance."""

    def __init__(
        self,
        persistence: RegisterFactPersistence,
        totals: TotalsMaintenanceCoordinator,
        domains: RegisterOperationDomainRegistry,
        validator: MovementValidator,
    ) -> None:
        self._persistence = persistence
        self._totals = totals
        self._domains = domains
        self._validator = validator

    def establish(self, movements: Sequence[Movement]) -> None:
        movements_tuple = tuple(movements)
        if not movements_tuple:
            return

        register_identity = self._single_register_identity(movements_tuple)
        self._validate(movements_tuple)
        domain = self._domains.get(register_identity)

        def operation() -> None:
            self._totals.ensure_mutation_admitted(register_identity)
            self._persistence.append(movements_tuple)

            for movement in movements_tuple:
                result = self._totals.apply(movement)
                self._ensure_totals_success(register_identity, result)

        domain.execute(operation)

    def remove(self, movements: Sequence[Movement]) -> None:
        movements_tuple = tuple(movements)
        if not movements_tuple:
            return

        register_identity = self._single_register_identity(movements_tuple)
        domain = self._domains.get(register_identity)

        def operation() -> None:
            self._totals.ensure_mutation_admitted(register_identity)
            self._persistence.remove(tuple(movement.identity for movement in movements_tuple))

            for movement in movements_tuple:
                result = self._totals.remove(movement)
                self._ensure_totals_success(register_identity, result)

        domain.execute(operation)

    def _validate(self, movements: tuple[Movement, ...]) -> None:
        movement_set: MovementSetLike = _MovementSet(movements)
        self._validator.validate(movement_set)

    @staticmethod
    def _single_register_identity(
        movements: Sequence[Movement],
    ) -> Identifier:
        register_identity = movements[0].register_identity

        if any(movement.register_identity != register_identity for movement in movements[1:]):
            raise ValueError("Register mutation must contain Movements for one Register")

        return register_identity

    @staticmethod
    def _ensure_totals_success(
        register_identity: Identifier,
        result: MaintenanceResult,
    ) -> None:
        from .maintenance import MaintenanceOutcome

        if result.outcome is MaintenanceOutcome.SUCCESS:
            return

        raise RegisterMutationMaintenanceError(
            register_identity,
            result,
        )
