from __future__ import annotations

from typing import Protocol

from accore.platform.registers import Movement

from .input import ValuationInput
from .key import ValuationKey


class ValuationKeyMapper(Protocol):
    """Map one posting movement to the generic valuation key."""

    def map(self, movement: Movement) -> ValuationKey: ...


class ValuationInputProvider(Protocol):
    """Provide semantic valuation input for one posting movement."""

    def provide(self, movement: Movement) -> ValuationInput: ...
