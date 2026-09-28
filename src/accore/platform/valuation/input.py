from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from accore.platform.foundation import Identifier

from .errors import ValuationValidationError
from .key import ValuationKey


@dataclass(frozen=True, slots=True)
class ValuationInput:
    """Immutable semantic valuation input derived from one posting movement."""

    valuation_key: ValuationKey
    quantity: Decimal
    document_identity: Identifier
    source_identity: Identifier
    occurred_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.quantity, Decimal) or self.quantity <= Decimal(0):
            raise ValuationValidationError("ValuationInput quantity must be a positive Decimal.")
