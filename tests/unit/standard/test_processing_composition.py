from __future__ import annotations

from unittest.mock import Mock

from accore.platform.registers import TotalsMaintenanceCoordinator
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
