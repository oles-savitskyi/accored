from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from accore.platform.foundation import Identifier

from .key import ValuationKey


@dataclass(frozen=True, slots=True)
class CostMovement:
    """Derived valuation movement materialized from authoritative valuation facts."""

    identity: Identifier
    valuation_key: ValuationKey
    quantity: Decimal
    cost: Decimal
    source_identity: Identifier
    created_at: datetime


@dataclass(frozen=True, slots=True)
class CostBalance:
    """Derived valuation balance materialized from authoritative valuation facts."""

    valuation_key: ValuationKey
    quantity: Decimal
    cost: Decimal
    calculated_at: datetime
