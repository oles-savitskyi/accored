from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol

from .key import ValuationKey
from .results import CostBalance, CostMovement


class CostTotalsReader(Protocol):
    """Read boundary for the current derived valuation cost balance."""

    def get(self, valuation_key: ValuationKey) -> CostBalance:
        """Return the current cost balance for one valuation key."""
        ...


class CostTotalsEngine(CostTotalsReader, Protocol):
    """Semantic Cost Totals Engine boundary."""

    def apply(self, movement: CostMovement) -> CostBalance:
        """Apply one signed cost movement."""
        ...

    def remove(self, movement: CostMovement) -> CostBalance:
        """Remove one signed cost movement."""
        ...

    def rebuild(self, valuation_key: ValuationKey, movements: Sequence[CostMovement]) -> None:
        """Rebuild one valuation key from authoritative cost movements."""
        ...


class DefaultCostTotalsEngine:
    """In-memory reference implementation of the valuation Cost Totals contract."""

    def __init__(self) -> None:
        self._balances: dict[ValuationKey, CostBalance] = {}

    def get(self, valuation_key: ValuationKey) -> CostBalance:
        return self._balances.get(
            valuation_key,
            CostBalance(
                valuation_key=valuation_key,
                quantity=Decimal(0),
                cost=Decimal(0),
                calculated_at=datetime.now(UTC),
            ),
        )

    def apply(self, movement: CostMovement) -> CostBalance:
        current = self.get(movement.valuation_key)
        balance = CostBalance(
            valuation_key=movement.valuation_key,
            quantity=current.quantity + movement.quantity,
            cost=current.cost + movement.cost,
            calculated_at=movement.created_at,
        )
        self._balances[movement.valuation_key] = balance
        return balance

    def remove(self, movement: CostMovement) -> CostBalance:
        current = self.get(movement.valuation_key)
        balance = CostBalance(
            valuation_key=movement.valuation_key,
            quantity=current.quantity - movement.quantity,
            cost=current.cost - movement.cost,
            calculated_at=movement.created_at,
        )
        self._balances[movement.valuation_key] = balance
        return balance

    def rebuild(self, valuation_key: ValuationKey, movements: Sequence[CostMovement]) -> None:
        quantity = sum((movement.quantity for movement in movements), Decimal(0))
        cost = sum((movement.cost for movement in movements), Decimal(0))
        calculated_at = max(
            (movement.created_at for movement in movements),
            default=datetime.now(UTC),
        )
        self._balances[valuation_key] = CostBalance(
            valuation_key=valuation_key,
            quantity=quantity,
            cost=cost,
            calculated_at=calculated_at,
        )
