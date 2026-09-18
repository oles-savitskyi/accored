from __future__ import annotations

from typing import Protocol

from accore.platform.object import ObjectInstance

from .movement_set import MovementSet


class PostingResultCoordinator(Protocol):
    def establish(self, document: ObjectInstance, movement_set: MovementSet) -> None: ...
    def remove(self, document: ObjectInstance) -> None: ...
