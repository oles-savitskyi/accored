from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import RLock
from typing import TYPE_CHECKING, Protocol

from accore.platform.foundation import Identifier

from .movement import Movement
from .totals import TotalsEngine, TotalsError

if TYPE_CHECKING:
    from accore.platform.persistence.facts import RegisterFactPersistence


class MaintenanceOperation(Enum):
    """Public Totals maintenance operation."""

    APPLY = "apply"
    REMOVE = "remove"
    REBUILD = "rebuild"


class TotalsLifecycleState(Enum):
    """Lifecycle state of the Totals maintenance subsystem."""

    CREATED = "created"
    ACTIVE = "active"
    MAINTENANCE = "maintenance"


class TotalsConsistencyState(Enum):
    """Consistency state of the published derived Totals."""

    VALID = "valid"
    INDETERMINATE = "indeterminate"
    RECOVERY_REQUIRED = "recovery_required"


@dataclass(frozen=True, slots=True)
class TotalsMaintenanceState:
    """Combined lifecycle and consistency state of Totals maintenance."""

    lifecycle: TotalsLifecycleState
    consistency: TotalsConsistencyState


class MaintenanceOutcome(Enum):
    """Expected outcome of a Totals maintenance operation."""

    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class MaintenanceResult:
    """Result of a Totals maintenance operation."""

    operation: MaintenanceOperation
    outcome: MaintenanceOutcome
    state: TotalsMaintenanceState


class TotalsMaintenanceCoordinator(Protocol):
    """Public boundary for Totals maintenance semantics."""

    def apply(self, movement: Movement) -> MaintenanceResult:
        """Apply one Movement contribution to derived Totals."""

    def remove(self, movement: Movement) -> MaintenanceResult:
        """Remove one Movement contribution from derived Totals."""

    def rebuild(self, register_identity: Identifier) -> MaintenanceResult:
        """Rebuild Register Totals from authoritative Movement Facts."""

    def recover(self, register_identity: Identifier) -> MaintenanceResult:
        """Recover Register Totals through authoritative reconstruction."""


class DefaultTotalsMaintenanceCoordinator:
    """Reference implementation of the Totals maintenance boundary."""

    def __init__(
        self,
        engine: TotalsEngine,
        persistence: RegisterFactPersistence,
    ) -> None:
        self._engine = engine
        self._persistence = persistence

        self._locks_guard = RLock()
        self._locks: dict[Identifier, RLock] = {}

        self._applied: dict[
            Identifier,
            set[tuple[Identifier, Identifier]],
        ] = {}
        self._states: dict[Identifier, TotalsMaintenanceState] = {}

    def apply(self, movement: Movement) -> MaintenanceResult:
        register_identity = movement.register_identity
        lock = self._lock_for(register_identity)

        with lock:
            state = self._state_for(register_identity)
            contribution_key = self._contribution_key(movement)

            if contribution_key in self._applied_for(register_identity):
                return self._success(
                    MaintenanceOperation.APPLY,
                    state,
                )

            self._states[register_identity] = self._maintenance_state(state)

            try:
                self._engine.apply(movement)
            except TotalsError:
                state = self._recovery_required_state()
                self._states[register_identity] = state

                return self._failure(
                    MaintenanceOperation.APPLY,
                    state,
                )
            except Exception:  # noqa: BLE001 — unexpected failures are explicitly indeterminate
                state = self._recovery_required_state()
                self._states[register_identity] = state

                return self._indeterminate(
                    MaintenanceOperation.APPLY,
                    state,
                )

            self._applied_for(register_identity).add(contribution_key)

            state = self._active_valid_state()
            self._states[register_identity] = state

            return self._success(
                MaintenanceOperation.APPLY,
                state,
            )

    def remove(self, movement: Movement) -> MaintenanceResult:
        register_identity = movement.register_identity
        lock = self._lock_for(register_identity)

        with lock:
            state = self._state_for(register_identity)
            contribution_key = self._contribution_key(movement)

            if contribution_key not in self._applied_for(register_identity):
                return self._success(
                    MaintenanceOperation.REMOVE,
                    state,
                )

            self._states[register_identity] = self._maintenance_state(state)

            try:
                self._engine.remove(movement)
            except TotalsError:
                state = self._recovery_required_state()
                self._states[register_identity] = state

                return self._failure(
                    MaintenanceOperation.REMOVE,
                    state,
                )
            except Exception:  # noqa: BLE001 — unexpected failures are explicitly indeterminate
                state = self._recovery_required_state()
                self._states[register_identity] = state

                return self._indeterminate(
                    MaintenanceOperation.REMOVE,
                    state,
                )

            self._applied_for(register_identity).remove(contribution_key)

            state = self._active_valid_state()
            self._states[register_identity] = state

            return self._success(
                MaintenanceOperation.REMOVE,
                state,
            )

    def rebuild(self, register_identity: Identifier) -> MaintenanceResult:
        from accore.platform.persistence.errors import (
            PersistenceError,
            PersistenceIndeterminateError,
        )

        lock = self._lock_for(register_identity)

        with lock:
            current_state = self._state_for(register_identity)
            self._states[register_identity] = self._maintenance_state(current_state)

            try:
                movements = self._persistence.enumerate(register_identity)
                self._engine.rebuild(register_identity, movements)
            except PersistenceIndeterminateError:
                state = self._recovery_required_state()
                self._states[register_identity] = state

                return self._indeterminate(
                    MaintenanceOperation.REBUILD,
                    state,
                )
            except PersistenceError:
                state = self._recovery_required_state()
                self._states[register_identity] = state

                return self._failure(
                    MaintenanceOperation.REBUILD,
                    state,
                )
            except TotalsError:
                state = self._recovery_required_state()
                self._states[register_identity] = state

                return self._failure(
                    MaintenanceOperation.REBUILD,
                    state,
                )
            except Exception:  # noqa: BLE001 — unexpected failures are explicitly indeterminate
                state = self._recovery_required_state()
                self._states[register_identity] = state

                return self._indeterminate(
                    MaintenanceOperation.REBUILD,
                    state,
                )

            self._applied[register_identity] = {
                self._contribution_key(movement) for movement in movements
            }

            state = self._active_valid_state()
            self._states[register_identity] = state

            return self._success(
                MaintenanceOperation.REBUILD,
                state,
            )

    def recover(self, register_identity: Identifier) -> MaintenanceResult:
        return self.rebuild(register_identity)

    def _lock_for(self, register_identity: Identifier) -> RLock:
        with self._locks_guard:
            lock = self._locks.get(register_identity)

            if lock is None:
                lock = RLock()
                self._locks[register_identity] = lock

            return lock

    def _applied_for(
        self,
        register_identity: Identifier,
    ) -> set[tuple[Identifier, Identifier]]:
        applied = self._applied.get(register_identity)

        if applied is None:
            applied = set()
            self._applied[register_identity] = applied

        return applied

    def _state_for(
        self,
        register_identity: Identifier,
    ) -> TotalsMaintenanceState:
        return self._states.get(
            register_identity,
            self._created_state(),
        )

    @staticmethod
    def _contribution_key(
        movement: Movement,
    ) -> tuple[Identifier, Identifier]:
        return movement.identity, movement.register_identity

    @staticmethod
    def _created_state() -> TotalsMaintenanceState:
        return TotalsMaintenanceState(
            lifecycle=TotalsLifecycleState.CREATED,
            consistency=TotalsConsistencyState.INDETERMINATE,
        )

    @staticmethod
    def _maintenance_state(
        state: TotalsMaintenanceState,
    ) -> TotalsMaintenanceState:
        return TotalsMaintenanceState(
            lifecycle=TotalsLifecycleState.MAINTENANCE,
            consistency=state.consistency,
        )

    @staticmethod
    def _active_valid_state() -> TotalsMaintenanceState:
        return TotalsMaintenanceState(
            lifecycle=TotalsLifecycleState.ACTIVE,
            consistency=TotalsConsistencyState.VALID,
        )

    @staticmethod
    def _recovery_required_state() -> TotalsMaintenanceState:
        return TotalsMaintenanceState(
            lifecycle=TotalsLifecycleState.ACTIVE,
            consistency=TotalsConsistencyState.RECOVERY_REQUIRED,
        )

    @staticmethod
    def _success(
        operation: MaintenanceOperation,
        state: TotalsMaintenanceState,
    ) -> MaintenanceResult:
        return MaintenanceResult(
            operation=operation,
            outcome=MaintenanceOutcome.SUCCESS,
            state=state,
        )

    @staticmethod
    def _failure(
        operation: MaintenanceOperation,
        state: TotalsMaintenanceState,
    ) -> MaintenanceResult:
        return MaintenanceResult(
            operation=operation,
            outcome=MaintenanceOutcome.FAILURE,
            state=state,
        )

    @staticmethod
    def _indeterminate(
        operation: MaintenanceOperation,
        state: TotalsMaintenanceState,
    ) -> MaintenanceResult:
        return MaintenanceResult(
            operation=operation,
            outcome=MaintenanceOutcome.INDETERMINATE,
            state=state,
        )
