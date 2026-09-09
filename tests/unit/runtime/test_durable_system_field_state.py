from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest

from accore.platform.foundation import Identifier
from accore.platform.runtime.durable_system_field_state import (
    DurableSystemFieldState,
)
from accore.platform.value.durable import (
    CollectionValue,
    DurableValue,
    DurableValueError,
    StructuredValue,
)


def make_identifier() -> Identifier:
    return Identifier.new()


def test_empty_creates_empty_state() -> None:
    state = DurableSystemFieldState.empty()

    assert len(state) == 0
    assert list(state) == []
    assert dict(state.items()) == {}


def test_empty_is_equal_to_empty_mapping() -> None:
    assert DurableSystemFieldState.empty() == DurableSystemFieldState({})


@pytest.mark.parametrize(
    ("identity", "value"),
    [
        ("deleted", True),
        ("version", 1),
        ("amount", Decimal("10.50")),
        ("name", "Document"),
        ("effective_date", date(2026, 9, 8)),
        ("updated_at", datetime(2026, 9, 8, 12, 30, tzinfo=UTC)),
    ],
)
def test_accepts_scalar_durable_values(
    identity: str,
    value: DurableValue,
) -> None:
    state = DurableSystemFieldState({identity: value})

    assert state[identity] == value


def test_accepts_structured_value() -> None:
    value = StructuredValue(
        {
            "source": "import",
            "attempt": 1,
        }
    )

    state = DurableSystemFieldState({"metadata": value})

    assert state["metadata"] == value


def test_accepts_collection_value() -> None:
    value = CollectionValue(
        (
            "first",
            2,
            Decimal("3.00"),
        )
    )

    state = DurableSystemFieldState({"history": value})

    assert state["history"] == value


def test_accepts_identifier_as_system_field_value() -> None:
    parent_identity = make_identifier()

    state = DurableSystemFieldState(
        {
            "parent_id": parent_identity,
        }
    )

    assert state["parent_id"] == parent_identity


def test_accepts_explicit_null() -> None:
    state = DurableSystemFieldState(
        {
            "parent_id": None,
        }
    )

    assert "parent_id" in state
    assert state["parent_id"] is None


def test_missing_is_not_null() -> None:
    state = DurableSystemFieldState.empty()

    assert "parent_id" not in state
    assert state.get("parent_id") is None

    with pytest.raises(KeyError):
        _ = state["parent_id"]


def test_explicit_null_is_not_missing() -> None:
    state = DurableSystemFieldState(
        {
            "parent_id": None,
        }
    )

    assert "parent_id" in state
    assert state["parent_id"] is None


@pytest.mark.parametrize(
    "identity",
    [
        "",
        " ",
        "   ",
        "\t",
        "\n",
    ],
)
def test_rejects_empty_or_whitespace_system_field_identity(
    identity: str,
) -> None:
    with pytest.raises(DurableValueError):
        DurableSystemFieldState({"version": 1, identity: True})


@pytest.mark.parametrize(
    "identity",
    [
        1,
        None,
        object(),
        ("version",),
    ],
)
def test_rejects_non_string_system_field_identity(
    identity: Any,
) -> None:
    with pytest.raises(DurableValueError):
        DurableSystemFieldState(
            {
                identity: True,
            }
        )


@pytest.mark.parametrize(
    "value",
    [
        1.5,
        object(),
        {"not": "structured value"},
        ["not", "collection value"],
        {1, 2, 3},
    ],
)
def test_rejects_invalid_system_field_value(
    value: Any,
) -> None:
    with pytest.raises(DurableValueError):
        DurableSystemFieldState(
            {
                "invalid": value,
            }
        )


def test_source_mapping_is_snapshotted() -> None:
    source = {
        "version": 1,
    }

    state = DurableSystemFieldState(source)

    source["version"] = 2
    source["deleted"] = True

    assert state["version"] == 1
    assert "deleted" not in state


def test_source_mapping_deletion_does_not_change_state() -> None:
    source = {
        "version": 1,
    }

    state = DurableSystemFieldState(source)

    del source["version"]

    assert state["version"] == 1


def test_getitem_returns_existing_value() -> None:
    state = DurableSystemFieldState(
        {
            "version": 3,
        }
    )

    assert state["version"] == 3


def test_getitem_raises_key_error_for_missing_value() -> None:
    state = DurableSystemFieldState.empty()

    with pytest.raises(KeyError):
        _ = state["missing"]


def test_get_returns_existing_value() -> None:
    state = DurableSystemFieldState(
        {
            "version": 3,
        }
    )

    assert state.get("version") == 3


def test_get_returns_default_for_missing_value() -> None:
    state = DurableSystemFieldState.empty()

    assert state.get("missing") is None
    assert state.get("missing", 42) == 42


def test_contains_reports_system_field_presence() -> None:
    state = DurableSystemFieldState(
        {
            "version": 1,
        }
    )

    assert "version" in state
    assert "deleted" not in state


def test_len_returns_number_of_system_fields() -> None:
    state = DurableSystemFieldState(
        {
            "version": 1,
            "deleted": False,
            "parent_id": None,
        }
    )

    assert len(state) == 3


def test_iteration_returns_system_field_identities() -> None:
    state = DurableSystemFieldState(
        {
            "version": 1,
            "deleted": False,
        }
    )

    assert set(state) == {"version", "deleted"}


def test_keys_returns_system_field_identities() -> None:
    state = DurableSystemFieldState(
        {
            "version": 1,
            "deleted": False,
        }
    )

    assert set(state.keys()) == {"version", "deleted"}


def test_values_returns_system_field_values() -> None:
    parent_identity = make_identifier()

    state = DurableSystemFieldState(
        {
            "version": 1,
            "parent_id": parent_identity,
            "deleted": None,
        }
    )

    values = list(state.values())

    assert 1 in values
    assert parent_identity in values
    assert None in values


def test_items_returns_system_field_pairs() -> None:
    state = DurableSystemFieldState(
        {
            "version": 1,
            "deleted": False,
        }
    )

    assert dict(state.items()) == {
        "version": 1,
        "deleted": False,
    }


def test_state_has_no_mutation_api() -> None:
    state = DurableSystemFieldState.empty()

    assert not hasattr(state, "set")
    assert not hasattr(state, "update")
    assert not hasattr(state, "pop")
    assert not hasattr(state, "clear")
    assert not hasattr(state, "popitem")
    assert not hasattr(state, "setdefault")
    assert not hasattr(state, "__setitem__")


def test_equal_states_have_equal_semantics() -> None:
    parent_identity = make_identifier()

    left = DurableSystemFieldState(
        {
            "version": 1,
            "parent_id": parent_identity,
        }
    )
    right = DurableSystemFieldState(
        {
            "version": 1,
            "parent_id": parent_identity,
        }
    )

    assert left == right


def test_system_field_key_order_does_not_affect_equality() -> None:
    left = DurableSystemFieldState(
        {
            "version": 1,
            "deleted": False,
        }
    )
    right = DurableSystemFieldState(
        {
            "deleted": False,
            "version": 1,
        }
    )

    assert left == right


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (
            DurableSystemFieldState({"version": 1}),
            DurableSystemFieldState({"version": 2}),
        ),
        (
            DurableSystemFieldState({"version": 1}),
            DurableSystemFieldState({"deleted": True}),
        ),
        (
            DurableSystemFieldState({"parent_id": None}),
            DurableSystemFieldState({"parent_id": make_identifier()}),
        ),
        (
            DurableSystemFieldState.empty(),
            DurableSystemFieldState({"version": 1}),
        ),
    ],
)
def test_different_states_are_not_equal(
    left: DurableSystemFieldState,
    right: DurableSystemFieldState,
) -> None:
    assert left != right


def test_identifier_is_preserved_as_identifier() -> None:
    parent_identity = make_identifier()

    state = DurableSystemFieldState(
        {
            "parent_id": parent_identity,
        }
    )

    assert state["parent_id"] is parent_identity


def test_runtime_object_is_rejected() -> None:
    class FakeRuntimeObject:
        pass

    with pytest.raises(DurableValueError):
        DurableSystemFieldState(
            {
                "invalid": FakeRuntimeObject(),
            }
        )


def test_no_automatic_defaults_are_added() -> None:
    state = DurableSystemFieldState(
        {
            "version": 1,
        }
    )

    assert "created_at" not in state
    assert "updated_at" not in state
    assert "deleted" not in state


def test_no_object_identity_field_is_added_automatically() -> None:
    state = DurableSystemFieldState(
        {
            "version": 1,
        }
    )

    assert "id" not in state


def test_repr_contains_class_name_and_values() -> None:
    state = DurableSystemFieldState(
        {
            "version": 1,
        }
    )

    representation = repr(state)

    assert representation.startswith("DurableSystemFieldState(")
    assert "version" in representation
