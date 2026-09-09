from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from accore.platform.foundation.identity import Identifier
from accore.platform.persistence.system_field_state import (
    PersistentSystemFieldState,
)


def test_empty_state() -> None:
    state = PersistentSystemFieldState.empty()

    assert len(state) == 0
    assert list(state) == []
    assert dict(state.items()) == {}


def test_durable_scalar_values_are_supported() -> None:
    created_at = datetime.now(UTC)

    state = PersistentSystemFieldState(
        {
            "is_folder": True,
            "deleted": False,
            "version": 7,
            "amount": Decimal("12.50"),
            "name": "Example",
            "date": date(2026, 9, 9),
            "created_at": created_at,
        }
    )

    assert state["is_folder"] is True
    assert state["deleted"] is False
    assert state["version"] == 7
    assert state["amount"] == Decimal("12.50")
    assert state["name"] == "Example"
    assert state["date"] == date(2026, 9, 9)
    assert state["created_at"] == created_at


def test_identifier_value_is_supported() -> None:
    parent_id = Identifier.new()

    state = PersistentSystemFieldState({"parent_id": parent_id})

    assert state["parent_id"] == parent_id


def test_null_value_is_supported() -> None:
    state = PersistentSystemFieldState({"parent_id": None})

    assert "parent_id" in state
    assert state["parent_id"] is None


def test_missing_value_is_distinct_from_null() -> None:
    state = PersistentSystemFieldState({"parent_id": None})

    assert "parent_id" in state
    assert state["parent_id"] is None
    assert "deleted" not in state


def test_structured_durable_value_is_supported() -> None:
    from accore.platform.value.durable import StructuredValue

    value = StructuredValue(
        {
            "source": "system",
            "sequence": 3,
        }
    )

    state = PersistentSystemFieldState({"metadata": value})

    assert state["metadata"] == value


def test_collection_durable_value_is_supported() -> None:
    from accore.platform.value.durable import CollectionValue

    value = CollectionValue(("a", 1, True))

    state = PersistentSystemFieldState({"payload": value})

    assert state["payload"] == value


def test_invalid_system_field_name_is_rejected() -> None:
    with pytest.raises(ValueError, match="system field name"):
        PersistentSystemFieldState({"": True})


def test_whitespace_system_field_name_is_rejected() -> None:
    with pytest.raises(ValueError, match="system field name"):
        PersistentSystemFieldState({"   ": True})


def test_non_string_system_field_name_is_rejected() -> None:
    with pytest.raises(ValueError, match="system field name"):
        PersistentSystemFieldState({123: True})  # type: ignore[dict-item]


def test_float_is_not_a_durable_value() -> None:
    with pytest.raises((TypeError, ValueError)):
        PersistentSystemFieldState({"value": 1.5})  # type: ignore[dict-item]


def test_arbitrary_object_is_not_supported() -> None:
    with pytest.raises((TypeError, ValueError)):
        PersistentSystemFieldState({"value": object()})  # type: ignore[dict-item]


def test_identifier_is_not_coerced() -> None:
    identifier = Identifier.new()

    state = PersistentSystemFieldState({"parent_id": identifier})

    assert state["parent_id"] is identifier


def test_state_is_immutable() -> None:
    state = PersistentSystemFieldState({"deleted": False})

    with pytest.raises(TypeError):
        state["deleted"] = True  # type: ignore[index]


def test_snapshot_is_independent_from_source_mapping() -> None:
    source = {"deleted": False}

    state = PersistentSystemFieldState(source)

    source["deleted"] = True
    source["version"] = 2

    assert state["deleted"] is False
    assert "version" not in state


def test_keys_values_and_items_are_read_only_views() -> None:
    parent_id = Identifier.new()

    state = PersistentSystemFieldState(
        {
            "parent_id": parent_id,
            "deleted": False,
        }
    )

    assert set(state.keys()) == {"parent_id", "deleted"}
    assert list(state.values()) == [parent_id, False]
    assert list(state.items()) == [
        ("parent_id", parent_id),
        ("deleted", False),
    ]


def test_equality_is_value_based() -> None:
    parent_id = Identifier.new()

    first = PersistentSystemFieldState({"parent_id": parent_id})
    second = PersistentSystemFieldState({"parent_id": parent_id})

    assert first == second


def test_different_states_are_not_equal() -> None:
    first = PersistentSystemFieldState({"version": 1})
    second = PersistentSystemFieldState({"version": 2})

    assert first != second


def test_multiple_system_fields_are_supported() -> None:
    parent_id = Identifier.new()

    state = PersistentSystemFieldState(
        {
            "parent_id": parent_id,
            "is_folder": True,
            "deleted": False,
            "version": 4,
        }
    )

    assert len(state) == 4
    assert state["parent_id"] == parent_id
    assert state["is_folder"] is True
    assert state["deleted"] is False
    assert state["version"] == 4


def test_repr_is_available() -> None:
    state = PersistentSystemFieldState({"deleted": False})

    assert "PersistentSystemFieldState" in repr(state)
