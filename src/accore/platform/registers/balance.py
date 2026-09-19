from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from accore.platform.foundation import Identifier

from .totals import TotalsKey, TotalsReader, TotalValue


class BalanceQueryError(Exception):
    """Base error for Balance Query failures."""


class BalanceQueryValidationError(BalanceQueryError, ValueError):
    """Raised when a Balance Query violates semantic input invariants."""


@dataclass(frozen=True, slots=True)
class BalanceQuery:
    """Immutable request for one concrete Register aggregation scope."""

    register_identity: Identifier
    aggregation_scope: TotalsKey

    def __post_init__(self) -> None:
        if self.register_identity is None:
            raise BalanceQueryValidationError("Balance Query requires a Register identity.")
        if self.aggregation_scope is None:
            raise BalanceQueryValidationError("Balance Query requires an aggregation scope.")


@dataclass(frozen=True, slots=True)
class BalanceResult:
    """Immutable current Balance for one concrete Register aggregation scope."""

    register_identity: Identifier
    aggregation_scope: TotalsKey
    value: TotalValue

    def __post_init__(self) -> None:
        if self.register_identity is None:
            raise BalanceQueryValidationError("Balance Result requires a Register identity.")
        if self.aggregation_scope is None:
            raise BalanceQueryValidationError("Balance Result requires an aggregation scope.")
        if not isinstance(self.value, Decimal):
            raise BalanceQueryValidationError("Balance Result value must be Decimal.")


class BalanceQueryService(Protocol):
    """Public semantic boundary for current Balance queries."""

    def query(self, query: BalanceQuery) -> BalanceResult:
        """Return the current Balance for one concrete aggregation scope."""


class DefaultBalanceQueryService:
    """Reference Balance Query implementation over the Totals read boundary."""

    def __init__(self, totals: TotalsReader) -> None:
        self._totals = totals

    def query(self, query: BalanceQuery) -> BalanceResult:
        value = self._totals.get(query.register_identity, query.aggregation_scope)
        return BalanceResult(
            register_identity=query.register_identity,
            aggregation_scope=query.aggregation_scope,
            value=value,
        )
