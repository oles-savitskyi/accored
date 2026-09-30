from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from accore.platform.foundation import Identifier
from accore.platform.valuation import (
    DefaultValuationPreparationStateFactory,
    ProjectedValuationPreparationState,
    ValuationConsumption,
    ValuationFact,
    ValuationFactPersistence,
    ValuationKey,
    ValuationLayer,
    ValuationReversal,
    ValuationValidationError,
)


class InMemoryFacts(ValuationFactPersistence):
    def __init__(self, facts: tuple[ValuationFact, ...]) -> None:
        self._facts = facts

    def append(self, facts: Sequence[ValuationFact]) -> None:
        self._facts = (*self._facts, *facts)

    def find(self, identity: Identifier) -> ValuationFact | None:
        return next((fact for fact in self._facts if fact.identity == identity), None)

    def find_by_source_document(self, document_identity: Identifier) -> tuple[ValuationFact, ...]:
        return tuple(self._facts)

    def find_by_source_movement(self, movement_identity: Identifier) -> tuple[ValuationFact, ...]:
        return tuple(self._facts)

    def find_by_valuation_key(self, valuation_key: ValuationKey) -> tuple[ValuationFact, ...]:
        return tuple(fact for fact in self._facts if fact.valuation_key == valuation_key)

    def enumerate(self) -> tuple[ValuationFact, ...]:
        return self._facts


def identifier(value: str) -> Identifier:
    return Identifier.from_str(value)


def key() -> ValuationKey:
    return ValuationKey({"product": "PR-01", "warehouse": "WH-01"})


def layer(
    value: str,
    document: Identifier,
    *,
    quantity: str = "10",
    cost: str = "100",
    created_at: datetime | None = None,
) -> ValuationLayer:
    return ValuationLayer(
        identity=identifier(value),
        valuation_key=key(),
        quantity=Decimal(quantity),
        total_cost=Decimal(cost),
        source_document_identity=document,
        source_movement_identity=Identifier.new(),
        created_at=created_at or datetime(2026, 9, 25, 10, 0, tzinfo=UTC),
    )


def consumption(
    value: str,
    document: Identifier,
    layer_identity: Identifier,
    *,
    quantity: str = "3",
    cost: str = "30",
) -> ValuationConsumption:
    return ValuationConsumption(
        identity=identifier(value),
        valuation_key=key(),
        layer_identity=layer_identity,
        quantity=Decimal(quantity),
        cost=Decimal(cost),
        document_identity=document,
        source_identity=Identifier.new(),
        created_at=datetime(2026, 9, 26, 10, 0, tzinfo=UTC),
    )


def test_authoritative_state_reconstructs_current_available_layers() -> None:
    source_document = identifier("00000000000000000000000001")
    facts = InMemoryFacts((layer("00000000000000000000000002", source_document),))

    state = DefaultValuationPreparationStateFactory(facts).authoritative()

    available = state.find_available_layers(key())
    assert available == facts.enumerate()
    assert isinstance(state, ProjectedValuationPreparationState)


def test_replacement_removes_old_layer_from_projected_state() -> None:
    old_document = identifier("00000000000000000000000001")
    other_document = identifier("00000000000000000000000002")
    old_layer = layer("00000000000000000000000003", old_document)
    other_layer = layer("00000000000000000000000004", other_document)
    facts = InMemoryFacts((old_layer, other_layer))

    state = DefaultValuationPreparationStateFactory(facts).for_replacement(old_document)

    assert state.find_available_layers(key()) == (other_layer,)
    assert facts.enumerate() == (old_layer, other_layer)


def test_replacement_restores_old_consumption_before_removing_old_layer() -> None:
    old_document = identifier("00000000000000000000000001")
    other_document = identifier("00000000000000000000000002")
    source_layer = layer("00000000000000000000000003", other_document)
    old_layer = layer("00000000000000000000000004", old_document, quantity="5", cost="50")
    old_consumption = consumption(
        "00000000000000000000000005",
        old_document,
        source_layer.identity,
        quantity="4",
        cost="40",
    )
    facts = InMemoryFacts((source_layer, old_layer, old_consumption))

    state = DefaultValuationPreparationStateFactory(facts).for_replacement(old_document)

    assert state.find_available_layers(key()) == (source_layer,)
    assert source_layer.quantity == Decimal(10)
    assert facts.enumerate() == (source_layer, old_layer, old_consumption)


def test_replacement_projects_combined_old_consumption_and_old_establishment() -> None:
    old_document = identifier("00000000000000000000000001")
    other_document = identifier("00000000000000000000000002")
    source_layer = layer("00000000000000000000000003", other_document)
    old_layer = layer("00000000000000000000000004", old_document, quantity="5", cost="50")
    old_consumption = consumption(
        "00000000000000000000000005",
        old_document,
        source_layer.identity,
        quantity="4",
        cost="40",
    )
    facts = InMemoryFacts((source_layer, old_layer, old_consumption))

    state = DefaultValuationPreparationStateFactory(facts).for_replacement(old_document)

    assert state.find_available_layers(key()) == (source_layer,)
    assert state.find_available_layers(key())[0].quantity == Decimal(10)
    assert state.find_available_layers(key())[0].total_cost == Decimal(100)


def test_replacement_rejects_layer_consumed_by_another_document() -> None:
    old_document = identifier("00000000000000000000000001")
    other_document = identifier("00000000000000000000000002")
    old_layer = layer("00000000000000000000000003", old_document)
    external_consumption = consumption(
        "00000000000000000000000004",
        other_document,
        old_layer.identity,
    )
    facts = InMemoryFacts((old_layer, external_consumption))

    with pytest.raises(ValuationValidationError, match="another document consumes it"):
        DefaultValuationPreparationStateFactory(facts).for_replacement(old_document)


def test_replacement_is_deterministic_and_does_not_persist_reversals() -> None:
    old_document = identifier("00000000000000000000000001")
    other_document = identifier("00000000000000000000000002")
    source_layer = layer("00000000000000000000000003", other_document)
    old_layer = layer("00000000000000000000000004", old_document)
    old_consumption = consumption(
        "00000000000000000000000005",
        old_document,
        source_layer.identity,
    )
    facts = InMemoryFacts((source_layer, old_layer, old_consumption))
    factory = DefaultValuationPreparationStateFactory(facts)

    first = factory.for_replacement(old_document)
    second = factory.for_replacement(old_document)

    assert first == second
    assert not any(isinstance(fact, ValuationReversal) for fact in facts.enumerate())
    assert facts.enumerate() == (source_layer, old_layer, old_consumption)
