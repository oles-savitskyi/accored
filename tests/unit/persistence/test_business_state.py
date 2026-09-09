from __future__ import annotations

import pytest

from accore.platform.foundation.identity import Identifier
from accore.platform.persistence.business_state import PersistentBusinessState


def test_empty_state() -> None:
    state = PersistentBusinessState.empty()

    assert len(state) == 0
    assert list(state) == []
    assert dict(state.items()) == {}


def test_business_state_maps_definition_to_current_value() -> None:
    definition_identity = Identifier.new()
    state_identity = Identifier.new()

    state = PersistentBusinessState({definition_identity: state_identity})

    assert state[definition_identity] == state_identity
    assert state.get(definition_identity) == state_identity
    assert definition_identity in state


def test_missing_definition_is_distinct_from_present_value() -> None:
    definition_identity = Identifier.new()
    state_identity = Identifier.new()

    state = PersistentBusinessState({definition_identity: state_identity})

    missing_identity = Identifier.new()

    assert definition_identity in state
    assert missing_identity not in state
    assert state.get(missing_identity) is None


def test_definition_identity_must_be_identifier() -> None:
    with pytest.raises(TypeError, match="Identifier"):
        PersistentBusinessState({"invalid": Identifier.new()})  # type: ignore[dict-item]


def test_state_value_identity_must_be_identifier() -> None:
    with pytest.raises(TypeError, match="Identifier"):
        PersistentBusinessState({Identifier.new(): "invalid"})  # type: ignore[dict-item]


def test_none_definition_identity_is_rejected() -> None:
    with pytest.raises(TypeError, match="Identifier"):
        PersistentBusinessState({None: Identifier.new()})  # type: ignore[dict-item]


def test_none_state_value_identity_is_rejected() -> None:
    with pytest.raises(TypeError, match="Identifier"):
        PersistentBusinessState({Identifier.new(): None})  # type: ignore[dict-item]


def test_state_is_immutable() -> None:
    definition_identity = Identifier.new()
    state_identity = Identifier.new()

    state = PersistentBusinessState({definition_identity: state_identity})

    with pytest.raises(TypeError):
        state[definition_identity] = Identifier.new()  # type: ignore[index]


def test_snapshot_is_independent_from_source_mapping() -> None:
    definition_identity = Identifier.new()
    state_identity = Identifier.new()

    source = {definition_identity: state_identity}

    state = PersistentBusinessState(source)

    replacement = Identifier.new()
    source[definition_identity] = replacement
    source[Identifier.new()] = Identifier.new()

    assert state[definition_identity] == state_identity
    assert len(state) == 1


def test_keys_values_and_items_are_read_only_views() -> None:
    first_definition = Identifier.new()
    first_state = Identifier.new()
    second_definition = Identifier.new()
    second_state = Identifier.new()

    state = PersistentBusinessState(
        {
            first_definition: first_state,
            second_definition: second_state,
        }
    )

    assert set(state.keys()) == {
        first_definition,
        second_definition,
    }
    assert list(state.values()) == [
        first_state,
        second_state,
    ]
    assert list(state.items()) == [
        (first_definition, first_state),
        (second_definition, second_state),
    ]


def test_equality_is_value_based() -> None:
    definition_identity = Identifier.new()
    state_identity = Identifier.new()

    first = PersistentBusinessState({definition_identity: state_identity})
    second = PersistentBusinessState({definition_identity: state_identity})

    assert first == second


def test_different_states_are_not_equal() -> None:
    definition_identity = Identifier.new()

    first = PersistentBusinessState({definition_identity: Identifier.new()})
    second = PersistentBusinessState({definition_identity: Identifier.new()})

    assert first != second


def test_multiple_business_state_definitions_are_supported() -> None:
    first_definition = Identifier.new()
    first_state = Identifier.new()
    second_definition = Identifier.new()
    second_state = Identifier.new()

    state = PersistentBusinessState(
        {
            first_definition: first_state,
            second_definition: second_state,
        }
    )

    assert len(state) == 2
    assert state[first_definition] == first_state
    assert state[second_definition] == second_state


def test_repr_is_available() -> None:
    definition_identity = Identifier.new()
    state_identity = Identifier.new()

    state = PersistentBusinessState({definition_identity: state_identity})

    assert "PersistentBusinessState" in repr(state)
