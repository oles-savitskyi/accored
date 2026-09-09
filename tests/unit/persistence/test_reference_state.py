from __future__ import annotations

import pytest

from accore.platform.foundation.identity import Identifier
from accore.platform.persistence.reference_state import (
    PersistentReferenceState,
)


def test_empty_state() -> None:
    state = PersistentReferenceState.empty()

    assert len(state) == 0
    assert list(state) == []
    assert dict(state.items()) == {}


def test_single_identifier_reference() -> None:
    reference_id = Identifier.new()

    state = PersistentReferenceState({"customer": reference_id})

    assert state["customer"] == reference_id
    assert state.get("customer") == reference_id
    assert "customer" in state


def test_null_reference() -> None:
    state = PersistentReferenceState({"customer": None})

    assert "customer" in state
    assert state["customer"] is None


def test_empty_many_reference() -> None:
    state = PersistentReferenceState({"contacts": ()})

    assert state["contacts"] == ()


def test_many_reference_preserves_order() -> None:
    first = Identifier.new()
    second = Identifier.new()
    third = Identifier.new()

    state = PersistentReferenceState({"contacts": (first, second, third)})

    assert state["contacts"] == (first, second, third)


def test_many_reference_allows_duplicate_identifiers() -> None:
    reference_id = Identifier.new()

    state = PersistentReferenceState({"contacts": (reference_id, reference_id)})

    assert state["contacts"] == (reference_id, reference_id)


def test_missing_reference_is_distinct_from_null() -> None:
    state = PersistentReferenceState({"customer": None})

    assert "customer" not in PersistentReferenceState.empty()
    assert "customer" in state
    assert state["customer"] is None


def test_missing_reference_get_returns_none() -> None:
    state = PersistentReferenceState.empty()

    assert state.get("customer") is None


def test_invalid_reference_name_is_rejected() -> None:
    with pytest.raises(ValueError, match="reference name"):
        PersistentReferenceState({"": Identifier.new()})


def test_whitespace_reference_name_is_rejected() -> None:
    with pytest.raises(ValueError, match="reference name"):
        PersistentReferenceState({"   ": Identifier.new()})


def test_non_string_reference_name_is_rejected() -> None:
    with pytest.raises(ValueError, match="reference name"):
        PersistentReferenceState({123: Identifier.new()})  # type: ignore[dict-item]


def test_invalid_scalar_reference_value_is_rejected() -> None:
    with pytest.raises(TypeError, match="Identifier"):
        PersistentReferenceState({"customer": "customer-id"})  # type: ignore[dict-item]


def test_invalid_collection_reference_value_is_rejected() -> None:
    with pytest.raises(TypeError, match="tuple"):
        PersistentReferenceState({"contacts": [Identifier.new()]})  # type: ignore[dict-item]


def test_invalid_identifier_inside_collection_is_rejected() -> None:
    with pytest.raises(TypeError, match="Identifier"):
        PersistentReferenceState(
            {"contacts": (Identifier.new(), "invalid")}  # type: ignore[dict-item]
        )


def test_list_is_not_accepted_as_many_reference() -> None:
    with pytest.raises(TypeError):
        PersistentReferenceState({"contacts": []})  # type: ignore[dict-item]


def test_set_is_not_accepted_as_many_reference() -> None:
    with pytest.raises(TypeError):
        PersistentReferenceState({"contacts": {Identifier.new()}})  # type: ignore[dict-item]


def test_mapping_is_not_accepted_as_many_reference() -> None:
    with pytest.raises(TypeError):
        PersistentReferenceState({"contacts": {}})  # type: ignore[dict-item]


def test_state_is_immutable() -> None:
    state = PersistentReferenceState({"customer": Identifier.new()})

    with pytest.raises(TypeError):
        state["customer"] = Identifier.new()  # type: ignore[index]


def test_snapshot_is_independent_from_source_mapping() -> None:
    reference_id = Identifier.new()
    source = {"customer": reference_id}

    state = PersistentReferenceState(source)

    source["customer"] = Identifier.new()
    source["supplier"] = Identifier.new()

    assert state["customer"] == reference_id
    assert "supplier" not in state


def test_keys_values_and_items_are_read_only_views() -> None:
    reference_id = Identifier.new()

    state = PersistentReferenceState(
        {
            "customer": reference_id,
            "contacts": (),
        }
    )

    assert set(state.keys()) == {"customer", "contacts"}
    assert list(state.values()) == [reference_id, ()]
    assert list(state.items()) == [
        ("customer", reference_id),
        ("contacts", ()),
    ]


def test_equality_is_value_based() -> None:
    reference_id = Identifier.new()

    first = PersistentReferenceState({"customer": reference_id})
    second = PersistentReferenceState({"customer": reference_id})

    assert first == second


def test_different_states_are_not_equal() -> None:
    first = PersistentReferenceState({"customer": Identifier.new()})
    second = PersistentReferenceState({"customer": Identifier.new()})

    assert first != second


def test_repr_is_available() -> None:
    reference_id = Identifier.new()

    state = PersistentReferenceState({"customer": reference_id})

    assert "PersistentReferenceState" in repr(state)
