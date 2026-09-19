from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from accore.platform.foundation import Identifier

from .movement import Movement


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
