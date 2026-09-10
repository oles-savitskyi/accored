from dataclasses import dataclass
from inspect import signature

from accore.platform.persistence import RegisterFactPersistence


@dataclass(frozen=True)
class Movement:
    movement_id: str


class InMemoryRegisterFactPersistence:
    def __init__(self) -> None:
        self.movements: list[Movement] = []

    def append(self, movements: list[Movement]) -> None:
        self.movements.extend(movements)


def test_register_fact_persistence_contract_shape() -> None:
    assert list(signature(RegisterFactPersistence.append).parameters) == [
        "self",
        "movements",
    ]


def test_register_fact_persistence_is_append_only() -> None:
    persistence = InMemoryRegisterFactPersistence()
    movements = [Movement("m1"), Movement("m2")]

    assert persistence.append(movements) is None
    assert persistence.movements == movements
