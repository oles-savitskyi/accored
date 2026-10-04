from __future__ import annotations

from unittest.mock import Mock

from accore.platform.processing import DefaultProcessingRuntime
from accore.platform.registers import TotalsMaintenanceCoordinator
from accore.platform.security import AuthorizationService
from accore.platform.valuation import ValuationRebuilder
from standard.bootstrap import StandardConfigurationBootstrap
from standard.processings import (
    InventoryDerivedStateRebuildProcessing,
)


def test_compose_inventory_rebuild_processing_returns_standard_processing() -> None:
    register_maintenance = Mock(spec=TotalsMaintenanceCoordinator)
    valuation_rebuilder = Mock(spec=ValuationRebuilder)

    processing = StandardConfigurationBootstrap().compose_inventory_rebuild_processing(
        register_maintenance=register_maintenance,
        valuation_rebuilder=valuation_rebuilder,
    )

    assert isinstance(processing, InventoryDerivedStateRebuildProcessing)


class _AllowingAuthorizationService:
    def require(self, request: object) -> None:
        del request


def test_compose_processing_runtime_injects_authorization_service() -> None:
    authorization_service: AuthorizationService = _AllowingAuthorizationService()
    bootstrap = StandardConfigurationBootstrap()

    runtime = bootstrap.compose_processing_runtime({}, authorization_service)

    assert isinstance(runtime, DefaultProcessingRuntime)
    assert runtime is not None
