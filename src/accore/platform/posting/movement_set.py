from __future__ import annotations

from dataclasses import dataclass

from accore.platform.registers import Movement


@dataclass(frozen=True, slots=True)
class MovementSet:
    movements: tuple[Movement, ...]
