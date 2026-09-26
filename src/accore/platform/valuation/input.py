from __future__ import annotations

from dataclasses import dataclass

from .consumption import ConsumptionRequest
from .facts import ValuationLayer


@dataclass(frozen=True, slots=True)
class ValuationInput:
    """Immutable valuation input for an outbound consumption operation."""

    request: ConsumptionRequest
    layers: tuple[ValuationLayer, ...]
