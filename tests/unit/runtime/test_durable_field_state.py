from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from accore.platform.runtime.durable_field_state import DurableFieldState
from accore.platform.value.durable import (
    CollectionValue,
    DurableValueError,
    StructuredValue,
)


def test_empty_creates_empty_state() -> None:
    state = DurableFieldState.empty()

    assert len(state) == 0
    assert list(state) == []
    assert dict(state.items()) == {}


def test_empty_is_equal_to_empty_mapping() -> None:
    assert DurableFieldState.empty() == DurableFieldState({})


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("name", "Alice"),
        ("count", 10),
        ("amount", Decimal("125.50")),
        ("active", True),
        ("birth_date", __import__("datetime").date(2026, 9, 8)),
        (
            "created_at",
            __import__("datetime").datetime(2026, 9, 8, 12, 30),
        ),
        ("description", None),
    ],
)
def test_accepts_valid_field_values(
    key: str,
    value: Any,
) -> None:
    state = DurableFieldState({key: value})

    assert state[key] == value


@pytest.mark.parametrize(
    "key",
    [
        "",
        " ",
        "   ",
        "\t",
        "\n",
    ],
)
def test_rejects_invalid_field_identity(key: str) -> None:
    with pytest.raises(DurableValueError):
        DurableFieldState({key: "value"})


@pytest.mark.parametrize(
    "key",
    [
        1,
        None,
        object(),
        ("field",),
    ],
)
def test_rejects_non_string_field_identity(key: Any) -> None:
    with pytest.raises(DurableValueError):
        DurableFieldState({key: "value"})


@pytest.mark.parametrize(
    "value",
    [
        1.5,
        object(),
        {"nested": "value"},
        ["value"],
        {"value"},
    ],
)
def test_rejects_non_durable_values(value: Any) -> None:
    with pytest.raises(DurableValueError):
        DurableFieldState({"field": value})


def test_accepts_structured_value() -> None:
    value = StructuredValue({"name": "Alice", "age": 30})

    state = DurableFieldState({"profile": value})

    assert state["profile"] == value


def test_accepts_collection_value() -> None:
    value = CollectionValue(["one", 2, Decimal("3.50")])

    state = DurableFieldState({"items": value})

    assert state["items"] == value


def test_rejects_invalid_nested_structured_value() -> None:
    with pytest.raises(DurableValueError):
        StructuredValue({"name": 1.5})


def test_rejects_invalid_nested_collection_value() -> None:
    with pytest.raises(DurableValueError):
        CollectionValue(["valid", 1.5])


def test_none_represents_explicit_null() -> None:
    state = DurableFieldState({"description": None})

    assert "description" in state
    assert state["description"] is None


def test_missing_field_is_not_the_same_as_null() -> None:
    state = DurableFieldState({"description": None})

    assert "description" not in DurableFieldState.empty()
    assert "description" in state

    with pytest.raises(KeyError):
        _ = DurableFieldState.empty()["description"]


def test_getitem_returns_field_value() -> None:
    state = DurableFieldState({"name": "Alice"})

    assert state["name"] == "Alice"


def test_getitem_raises_key_error_for_missing_field() -> None:
    state = DurableFieldState.empty()

    with pytest.raises(KeyError):
        _ = state["missing"]


def test_get_returns_value_for_existing_field() -> None:
    state = DurableFieldState({"name": "Alice"})

    assert state.get("name") == "Alice"


def test_get_returns_default_for_missing_field() -> None:
    state = DurableFieldState.empty()

    assert state.get("missing") is None
    assert state.get("missing", "fallback") == "fallback"


def test_contains_reports_field_presence() -> None:
    state = DurableFieldState({"name": "Alice"})

    assert "name" in state
    assert "missing" not in state


def test_len_returns_number_of_fields() -> None:
    state = DurableFieldState(
        {
            "name": "Alice",
            "age": 30,
        }
    )

    assert len(state) == 2


def test_iteration_returns_field_identities() -> None:
    state = DurableFieldState(
        {
            "name": "Alice",
            "age": 30,
        }
    )

    assert set(state) == {"name", "age"}


def test_keys_returns_field_identities() -> None:
    state = DurableFieldState(
        {
            "name": "Alice",
            "age": 30,
        }
    )

    assert set(state.keys()) == {"name", "age"}


def test_values_returns_field_values() -> None:
    state = DurableFieldState(
        {
            "name": "Alice",
            "age": None,
        }
    )

    assert set(state.values()) == {"Alice", None}


def test_items_returns_field_pairs() -> None:
    state = DurableFieldState(
        {
            "name": "Alice",
            "age": 30,
        }
    )

    assert dict(state.items()) == {
        "name": "Alice",
        "age": 30,
    }


def test_source_mapping_is_snapshotted() -> None:
    source = {
        "name": "Alice",
    }

    state = DurableFieldState(source)

    source["name"] = "Bob"
    source["age"] = 30

    assert state["name"] == "Alice"
    assert "age" not in state


def test_source_mapping_deletion_does_not_change_state() -> None:
    source = {
        "name": "Alice",
        "age": 30,
    }

    state = DurableFieldState(source)

    del source["name"]

    assert state["name"] == "Alice"
    assert state["age"] == 30


def test_state_does_not_expose_mutation_through_mapping_api() -> None:
    state = DurableFieldState({"name": "Alice"})

    with pytest.raises(TypeError):
        state["name"] = "Bob"  # type: ignore[index]


def test_state_does_not_allow_field_deletion() -> None:
    state = DurableFieldState({"name": "Alice"})

    with pytest.raises(TypeError):
        del state["name"]  # type: ignore[misc]


def test_exposed_items_view_is_read_only() -> None:
    state = DurableFieldState({"name": "Alice"})

    items = state.items()

    assert dict(items) == {"name": "Alice"}


def test_equal_states_have_equal_semantics() -> None:
    left = DurableFieldState(
        {
            "name": "Alice",
            "age": 30,
        }
    )
    right = DurableFieldState(
        {
            "name": "Alice",
            "age": 30,
        }
    )

    assert left == right


def test_field_order_does_not_affect_equality() -> None:
    left = DurableFieldState(
        {
            "name": "Alice",
            "age": 30,
        }
    )
    right = DurableFieldState(
        {
            "age": 30,
            "name": "Alice",
        }
    )

    assert left == right


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (
            DurableFieldState({"name": "Alice"}),
            DurableFieldState({"name": "Bob"}),
        ),
        (
            DurableFieldState({"name": "Alice"}),
            DurableFieldState({"name": "Alice", "age": 30}),
        ),
        (
            DurableFieldState({"name": None}),
            DurableFieldState({"name": "Alice"}),
        ),
    ],
)
def test_different_states_are_not_equal(
    left: DurableFieldState,
    right: DurableFieldState,
) -> None:
    assert left != right


def test_null_equals_null() -> None:
    left = DurableFieldState({"description": None})
    right = DurableFieldState({"description": None})

    assert left == right


def test_mapping_values_are_not_implicitly_converted() -> None:
    with pytest.raises(DurableValueError):
        DurableFieldState({"payload": {"name": "Alice"}})

    with pytest.raises(DurableValueError):
        DurableFieldState({"items": ["one", "two"]})

    with pytest.raises(DurableValueError):
        DurableFieldState({"amount": 10.5})


def test_runtime_objects_are_not_durable_field_values() -> None:
    class FakeRuntimeObject:
        pass

    with pytest.raises(DurableValueError):
        DurableFieldState({"object": FakeRuntimeObject()})


def test_persistent_objects_are_not_durable_field_values() -> None:
    class FakePersistentObject:
        pass

    with pytest.raises(DurableValueError):
        DurableFieldState({"object": FakePersistentObject()})


def test_state_contains_only_field_semantics() -> None:
    state = DurableFieldState(
        {
            "name": "Alice",
            "amount": Decimal("100.00"),
            "description": None,
        }
    )

    assert dict(state.items()) == {
        "name": "Alice",
        "amount": Decimal("100.00"),
        "description": None,
    }


def test_mutation_methods_are_not_part_of_public_contract() -> None:
    state = DurableFieldState({"name": "Alice"})

    assert not hasattr(state, "set")
    assert not hasattr(state, "update")
    assert not hasattr(state, "pop")
    assert not hasattr(state, "clear")
    assert not hasattr(state, "popitem")
    assert not hasattr(state, "setdefault")


def test_structured_value_remains_immutable_through_field_state() -> None:
    value = StructuredValue(
        {
            "name": "Alice",
            "age": 30,
        }
    )
    state = DurableFieldState({"profile": value})

    assert state["profile"] == value
    assert state["profile"] is value


def test_collection_value_remains_immutable_through_field_state() -> None:
    value = CollectionValue(["one", "two"])
    state = DurableFieldState({"items": value})

    assert state["items"] == value
    assert state["items"] is value
