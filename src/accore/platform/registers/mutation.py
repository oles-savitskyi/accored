from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from accore.platform.foundation import Identifier

from .maintenance import MaintenanceResult, TotalsMaintenanceCoordinator
from .movement import Movement
from .operation_domain import RegisterOperationDomainRegistry

if TYPE_CHECKING:
    from accore.platform.persistence.facts import RegisterFactPersistence


class RegisterMutationOrchestrator:
    """Coordinate authoritative Movement mutation and derived Totals maintenance."""

    def __init__(
        self,
        persistence: RegisterFactPersistence,
        totals: TotalsMaintenanceCoordinator,
        domains: RegisterOperationDomainRegistry,
    ) -> None:
        self._persistence = persistence
        self._totals = totals
        self._domains = domains

    def establish(self, movements: Sequence[Movement]) -> None:
        movements_tuple = tuple(movements)
        if not movements_tuple:
            return

        register_identity = self._single_register_identity(movements_tuple)
        domain = self._domains.get(register_identity)

        def operation() -> None:
            self._persistence.append(movements_tuple)
            for movement in movements_tuple:
                result = self._totals.apply(movement)
                if not self._is_success(result):
                    raise RuntimeError(
                        "Totals maintenance did not successfully apply a persisted Movement"
                    )

        domain.execute(operation)

    def remove(self, movements: Sequence[Movement]) -> None:
        movements_tuple = tuple(movements)
        if not movements_tuple:
            return

        register_identity = self._single_register_identity(movements_tuple)
        domain = self._domains.get(register_identity)

        def operation() -> None:
            self._persistence.remove(tuple(movement.identity for movement in movements_tuple))
            for movement in movements_tuple:
                result = self._totals.remove(movement)
                if not self._is_success(result):
                    raise RuntimeError(
                        "Totals maintenance did not successfully remove a persisted Movement"
                    )

        domain.execute(operation)

    def rebuild(self, register_identity: Identifier) -> MaintenanceResult:
        domain = self._domains.get(register_identity)
        return domain.execute(
            lambda: self._rebuild_under_domain(register_identity),
        )

    def recover(self, register_identity: Identifier) -> MaintenanceResult:
        domain = self._domains.get(register_identity)
        return domain.execute(
            lambda: self._rebuild_under_domain(register_identity),
        )

    def _rebuild_under_domain(
        self,
        register_identity: Identifier,
    ) -> MaintenanceResult:
        return self._totals.rebuild(register_identity)

    @staticmethod
    def _single_register_identity(
        movements: Sequence[Movement],
    ) -> Identifier:
        register_identity = movements[0].register_identity
        if any(movement.register_identity != register_identity for movement in movements[1:]):
            raise ValueError("Register mutation must contain Movements for one Register")
        return register_identity

    @staticmethod
    def _is_success(result: MaintenanceResult) -> bool:
        from .maintenance import MaintenanceOutcome

        return result.outcome is MaintenanceOutcome.SUCCESS
