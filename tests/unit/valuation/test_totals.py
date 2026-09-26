from datetime import UTC, datetime
from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.valuation import CostMovement, DefaultCostTotalsEngine, ValuationKey


def test_apply_and_remove_maintain_signed_cost_balance() -> None:
    engine = DefaultCostTotalsEngine()
    key = ValuationKey({"product": "PR-01"})
    when = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)

    inbound = CostMovement(Identifier.new(), key, Decimal(10), Decimal(100), Identifier.new(), when)
    outbound = CostMovement(
        Identifier.new(), key, Decimal(-4), Decimal(-40), Identifier.new(), when
    )

    assert engine.apply(inbound).quantity == Decimal(10)
    balance = engine.apply(outbound)
    assert balance.quantity == Decimal(6)
    assert balance.cost == Decimal(60)

    balance = engine.remove(outbound)
    assert balance.quantity == Decimal(10)
    assert balance.cost == Decimal(100)


def test_rebuild_reconstructs_balance_from_movements() -> None:
    engine = DefaultCostTotalsEngine()
    key = ValuationKey({"product": "PR-01"})
    when = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)
    movements = (
        CostMovement(Identifier.new(), key, Decimal(10), Decimal(100), Identifier.new(), when),
        CostMovement(Identifier.new(), key, Decimal(-4), Decimal(-40), Identifier.new(), when),
    )

    engine.rebuild(key, movements)

    balance = engine.get(key)
    assert balance.quantity == Decimal(6)
    assert balance.cost == Decimal(60)
