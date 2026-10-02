from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.registers import TotalsKey
from accore.platform.reporting import ReportDataSourceIdentity
from accore.platform.valuation import CostBalance, ValuationKey
from standard.bootstrap import StandardConfigurationBootstrap
from standard.registers.inventory import INVENTORY_REGISTER_ID
from standard.reporting import INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY


class StubTotals:
    def enumerate(self, register_identity: Identifier) -> tuple[tuple[TotalsKey, Decimal], ...]:
        assert register_identity == INVENTORY_REGISTER_ID
        return ()

    def get(self, register_identity: Identifier, key: TotalsKey) -> Decimal:
        return Decimal(0)


class StubCostTotals:
    def enumerate(self) -> tuple[CostBalance, ...]:
        return ()

    def get(self, valuation_key: ValuationKey) -> CostBalance:
        raise AssertionError("get() should not be used during composition")


def test_bootstrap_composes_inventory_reporting_registry() -> None:
    registry = StandardConfigurationBootstrap().compose_inventory_reporting(
        StubTotals(),
        StubCostTotals(),
    )

    source = registry.get(ReportDataSourceIdentity(INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY.value))
    assert source.identity is INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY
