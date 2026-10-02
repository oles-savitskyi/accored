from datetime import UTC, datetime
from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.valuation import CostMovement, DefaultCostTotalsEngine, ValuationKey


def test_enumerate_returns_current_balances() -> None:
    engine = DefaultCostTotalsEngine()
    key = ValuationKey({"product": "P1", "warehouse": "W1"})
    movement = CostMovement(
        Identifier.new(),
        key,
        Decimal(5),
        Decimal(50),
        Identifier.new(),
        datetime(2026, 10, 1, tzinfo=UTC),
    )

    engine.apply(movement)

    assert engine.enumerate() == (engine.get(key),)
