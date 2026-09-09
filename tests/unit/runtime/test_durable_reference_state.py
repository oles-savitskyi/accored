from __future__ import annotations

from typing import Any

import pytest

from accore.platform.foundation.identity import Identifier
from accore.platform.runtime.durable_reference_state import (
    DurableReferenceState,
)
from accore.platform.value.durable import DurableValueError


def make_identity(value: str) -> Identifier:
    """Create an ObjectIdentity for tests.

    If ObjectIdentity uses a different construction API in the current
    implementation, this helper is the only place that needs adjustment.
    """
    return Identifier(value)


def test_empty_creates_empty_state() -> None:
    state = DurableReferenceState.empty()

    assert len(state) == 0
    assert list(state) == []
    assert dict(state.items()) == {}


def test_empty_is_equal_to_empty_mapping() -> None:
    assert DurableReferenceState.empty() == DurableReferenceState({})


def test_accepts_single_object_identity() -> None:
    identity = make_identity("01JTEST000000000000000001")

    state = DurableReferenceState({"customer": identity})

    assert state["customer"] == identity


def test_accepts_explicit_null_for_single_reference() -> None:
    state = DurableReferenceState({"customer": None})

    assert "customer" in state
    assert state["customer"] is None


def test_accepts_many_reference_as_tuple() -> None:
    first = make_identity("01JTEST000000000000000001")
    second = make_identity("01JTEST000000000000000002")

    state = DurableReferenceState(
        {
            "warehouses": (first, second),
        }
    )

    assert state["warehouses"] == (first, second)


def test_accepts_empty_many_reference() -> None:
    state = DurableReferenceState({"warehouses": ()})

    assert "warehouses" in state
    assert state["warehouses"] == ()


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
def test_rejects_invalid_reference_identity(key: str) -> None:
    with pytest.raises(DurableValueError):
        DurableReferenceState({key: make_identity("01JTEST000000000000000001")})


@pytest.mark.parametrize(
    "key",
    [
        1,
        None,
        object(),
        ("reference",),
    ],
)
def test_rejects_non_string_reference_identity(key: Any) -> None:
    with pytest.raises(DurableValueError):
        DurableReferenceState(
            {
                key: make_identity("01JTEST000000000000000001"),
            }
        )


@pytest.mark.parametrize(
    "value",
    [
        "01JTEST000000000000000001",
        42,
        1.5,
        object(),
        {},
        [],
        set(),
    ],
)
def test_rejects_invalid_single_reference_value(value: Any) -> None:
    with pytest.raises(DurableValueError):
        DurableReferenceState({"customer": value})


@pytest.mark.parametrize(
    "value",
    [
        ["01JTEST000000000000000001"],
        ["01JTEST000000000000000001", "01JTEST000000000000000002"],
        [make_identity("01JTEST000000000000000001")],
        {"01JTEST000000000000000001"},
    ],
)
def test_rejects_non_tuple_many_reference_value(value: Any) -> None:
    with pytest.raises(DurableValueError):
        DurableReferenceState({"warehouses": value})


def test_rejects_tuple_containing_non_object_identity() -> None:
    identity = make_identity("01JTEST000000000000000001")

    with pytest.raises(DurableValueError):
        DurableReferenceState(
            {
                "warehouses": (identity, "not-an-identity"),
            }
        )


def test_missing_reference_is_not_the_same_as_null() -> None:
    state = DurableReferenceState({"customer": None})

    empty = DurableReferenceState.empty()

    assert "customer" in state
    assert "customer" not in empty

    with pytest.raises(KeyError):
        _ = empty["customer"]


def test_empty_many_is_not_missing() -> None:
    state = DurableReferenceState({"warehouses": ()})

    assert "warehouses" in state
    assert state["warehouses"] == ()


def test_empty_many_is_not_null() -> None:
    state = DurableReferenceState({"warehouses": ()})

    assert state["warehouses"] is not None
    assert state["warehouses"] == ()


def test_getitem_returns_reference_value() -> None:
    identity = make_identity("01JTEST000000000000000001")

    state = DurableReferenceState({"customer": identity})

    assert state["customer"] == identity


def test_getitem_raises_key_error_for_missing_reference() -> None:
    state = DurableReferenceState.empty()

    with pytest.raises(KeyError):
        _ = state["missing"]


def test_get_returns_existing_reference() -> None:
    identity = make_identity("01JTEST000000000000000001")

    state = DurableReferenceState({"customer": identity})

    assert state.get("customer") == identity


def test_get_returns_default_for_missing_reference() -> None:
    state = DurableReferenceState.empty()

    assert state.get("missing") is None
    assert state.get("missing", ()) == ()


def test_contains_reports_reference_presence() -> None:
    state = DurableReferenceState(
        {
            "customer": make_identity("01JTEST000000000000000001"),
        }
    )

    assert "customer" in state
    assert "supplier" not in state


def test_len_returns_number_of_references() -> None:
    first = make_identity("01JTEST000000000000000001")
    second = make_identity("01JTEST000000000000000002")

    state = DurableReferenceState(
        {
            "customer": first,
            "supplier": second,
            "warehouses": (first, second),
        }
    )

    assert len(state) == 3


def test_iteration_returns_reference_identities() -> None:
    state = DurableReferenceState(
        {
            "customer": make_identity("01JTEST000000000000000001"),
            "supplier": make_identity("01JTEST000000000000000002"),
        }
    )

    assert set(state) == {"customer", "supplier"}


def test_keys_returns_reference_identities() -> None:
    state = DurableReferenceState(
        {
            "customer": make_identity("01JTEST000000000000000001"),
            "supplier": make_identity("01JTEST000000000000000002"),
        }
    )

    assert set(state.keys()) == {"customer", "supplier"}


def test_values_returns_reference_values() -> None:
    first = make_identity("01JTEST000000000000000001")

    state = DurableReferenceState(
        {
            "customer": first,
            "supplier": None,
        }
    )

    assert set(state.values()) == {first, None}


def test_items_returns_reference_pairs() -> None:
    first = make_identity("01JTEST000000000000000001")
    second = make_identity("01JTEST000000000000000002")

    state = DurableReferenceState(
        {
            "customer": first,
            "supplier": second,
        }
    )

    assert dict(state.items()) == {
        "customer": first,
        "supplier": second,
    }


def test_source_mapping_is_snapshotted() -> None:
    identity = make_identity("01JTEST000000000000000001")
    source = {
        "customer": identity,
    }

    state = DurableReferenceState(source)

    source["customer"] = None
    source["supplier"] = make_identity("01JTEST000000000000000002")

    assert state["customer"] == identity
    assert "supplier" not in state


def test_source_mapping_deletion_does_not_change_state() -> None:
    identity = make_identity("01JTEST000000000000000001")
    source = {
        "customer": identity,
    }

    state = DurableReferenceState(source)

    del source["customer"]

    assert state["customer"] == identity


def test_many_reference_tuple_is_not_mutable() -> None:
    first = make_identity("01JTEST000000000000000001")
    second = make_identity("01JTEST000000000000000002")

    state = DurableReferenceState(
        {
            "warehouses": (first, second),
        }
    )

    value = state["warehouses"]

    assert value == (first, second)

    with pytest.raises(TypeError):
        value[0] = second  # type: ignore[index]


def test_state_does_not_expose_mapping_mutation() -> None:
    identity = make_identity("01JTEST000000000000000001")
    state = DurableReferenceState({"customer": identity})

    with pytest.raises(TypeError):
        state["customer"] = None  # type: ignore[index]


def test_state_does_not_allow_reference_deletion() -> None:
    identity = make_identity("01JTEST000000000000000001")
    state = DurableReferenceState({"customer": identity})

    with pytest.raises(TypeError):
        del state["customer"]  # type: ignore[misc]


def test_equal_states_have_equal_semantics() -> None:
    first = make_identity("01JTEST000000000000000001")
    second = make_identity("01JTEST000000000000000002")

    left = DurableReferenceState(
        {
            "customer": first,
            "warehouses": (first, second),
        }
    )
    right = DurableReferenceState(
        {
            "customer": first,
            "warehouses": (first, second),
        }
    )

    assert left == right


def test_reference_key_order_does_not_affect_equality() -> None:
    first = make_identity("01JTEST000000000000000001")
    second = make_identity("01JTEST000000000000000002")

    left = DurableReferenceState(
        {
            "customer": first,
            "supplier": second,
        }
    )
    right = DurableReferenceState(
        {
            "supplier": second,
            "customer": first,
        }
    )

    assert left == right


def test_many_reference_element_order_affects_equality() -> None:
    first = make_identity("01JTEST000000000000000001")
    second = make_identity("01JTEST000000000000000002")

    left = DurableReferenceState(
        {
            "warehouses": (first, second),
        }
    )
    right = DurableReferenceState(
        {
            "warehouses": (second, first),
        }
    )

    assert left != right


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (
            DurableReferenceState({"customer": make_identity("01JTEST000000000000000001")}),
            DurableReferenceState({"customer": make_identity("01JTEST000000000000000002")}),
        ),
        (
            DurableReferenceState({"customer": make_identity("01JTEST000000000000000001")}),
            DurableReferenceState({"supplier": make_identity("01JTEST000000000000000001")}),
        ),
        (
            DurableReferenceState({"customer": None}),
            DurableReferenceState({"customer": make_identity("01JTEST000000000000000001")}),
        ),
        (
            DurableReferenceState({"warehouses": ()}),
            DurableReferenceState({"warehouses": (make_identity("01JTEST000000000000000001"),)}),
        ),
    ],
)
def test_different_states_are_not_equal(
    left: DurableReferenceState,
    right: DurableReferenceState,
) -> None:
    assert left != right


def test_null_equals_null() -> None:
    left = DurableReferenceState({"customer": None})
    right = DurableReferenceState({"customer": None})

    assert left == right


def test_empty_many_equals_empty_many() -> None:
    left = DurableReferenceState({"warehouses": ()})
    right = DurableReferenceState({"warehouses": ()})

    assert left == right


def test_runtime_objects_are_not_reference_values() -> None:
    class FakeRuntimeObject:
        pass

    with pytest.raises(DurableValueError):
        DurableReferenceState({"customer": FakeRuntimeObject()})


def test_persistent_objects_are_not_reference_values() -> None:
    class FakePersistentObject:
        pass

    with pytest.raises(DurableValueError):
        DurableReferenceState({"customer": FakePersistentObject()})


def test_reference_state_has_no_mutation_methods() -> None:
    state = DurableReferenceState.empty()

    assert not hasattr(state, "set")
    assert not hasattr(state, "update")
    assert not hasattr(state, "pop")
    assert not hasattr(state, "clear")
    assert not hasattr(state, "popitem")
    assert not hasattr(state, "setdefault")


def test_single_reference_stores_object_identity_only() -> None:
    identity = make_identity("01JTEST000000000000000001")

    state = DurableReferenceState({"customer": identity})

    assert state["customer"] is identity


def test_many_reference_preserves_object_identity_values() -> None:
    first = make_identity("01JTEST000000000000000001")
    second = make_identity("01JTEST000000000000000002")

    state = DurableReferenceState(
        {
            "warehouses": (first, second),
        }
    )

    assert state["warehouses"][0] is first
    assert state["warehouses"][1] is second
