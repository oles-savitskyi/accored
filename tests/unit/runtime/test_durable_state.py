from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.runtime.business_state import BusinessStateSnapshot
from accore.platform.runtime.durable_field_state import DurableFieldState
from accore.platform.runtime.durable_reference_state import DurableReferenceState
from accore.platform.runtime.durable_state import RuntimeDurableState
from accore.platform.runtime.durable_system_field_state import (
    DurableSystemFieldState,
)
from accore.platform.value.durable import CollectionValue, StructuredValue


def test_empty_creates_empty_state() -> None:
    state = RuntimeDurableState.empty()

    assert state.fields == DurableFieldState.empty()
    assert state.references == DurableReferenceState.empty()
    assert state.business_state == BusinessStateSnapshot.empty()
    assert state.system_fields == DurableSystemFieldState.empty()


def test_empty_has_stable_four_part_shape() -> None:
    state = RuntimeDurableState.empty()

    assert len(state.fields) == 0
    assert len(state.references) == 0
    assert len(state.business_state) == 0
    assert len(state.system_fields) == 0


def test_state_preserves_component_identity() -> None:
    fields = DurableFieldState({"name": "Invoice"})
    references = DurableReferenceState({"customer": Identifier.new()})
    business_state = BusinessStateSnapshot({})
    system_fields = DurableSystemFieldState({"deleted": False})

    state = RuntimeDurableState(
        fields=fields,
        references=references,
        business_state=business_state,
        system_fields=system_fields,
    )

    assert state.fields is fields
    assert state.references is references
    assert state.business_state is business_state
    assert state.system_fields is system_fields


def test_state_is_immutable() -> None:
    state = RuntimeDurableState.empty()

    try:
        state.fields = DurableFieldState.empty()
    except AttributeError:
        pass
    else:
        raise AssertionError("RuntimeDurableState must be immutable")


def test_equal_states_are_equal() -> None:
    state_a = RuntimeDurableState(
        fields=DurableFieldState(
            {
                "name": "Invoice",
                "amount": Decimal("125.50"),
                "active": True,
            }
        ),
        references=DurableReferenceState(
            {
                "customer": Identifier.new(),
            }
        ),
        business_state=BusinessStateSnapshot({}),
        system_fields=DurableSystemFieldState(
            {
                "deleted": False,
                "created_at": datetime(
                    2026,
                    9,
                    8,
                    12,
                    30,
                    tzinfo=UTC,
                ),
            }
        ),
    )

    state_b = RuntimeDurableState(
        fields=state_a.fields,
        references=state_a.references,
        business_state=state_a.business_state,
        system_fields=state_a.system_fields,
    )

    assert state_a == state_b


def test_different_components_make_states_different() -> None:
    state_a = RuntimeDurableState.empty()

    state_b = RuntimeDurableState(
        fields=DurableFieldState({"name": "Invoice"}),
        references=DurableReferenceState.empty(),
        business_state=BusinessStateSnapshot.empty(),
        system_fields=DurableSystemFieldState.empty(),
    )

    assert state_a != state_b


def test_all_durable_value_shapes_can_be_composed() -> None:
    state = RuntimeDurableState(
        fields=DurableFieldState(
            {
                "boolean": True,
                "integer": 42,
                "decimal": Decimal("10.25"),
                "string": "value",
                "date": date(2026, 9, 8),
                "datetime": datetime(
                    2026,
                    9,
                    8,
                    12,
                    30,
                    tzinfo=UTC,
                ),
                "structured": StructuredValue(
                    {
                        "nested": "value",
                    }
                ),
                "collection": CollectionValue(
                    (
                        "first",
                        Decimal("2.50"),
                    )
                ),
            }
        ),
        references=DurableReferenceState(
            {
                "parent": Identifier.new(),
                "children": (),
            }
        ),
        business_state=BusinessStateSnapshot({}),
        system_fields=DurableSystemFieldState(
            {
                "deleted": False,
                "version": 1,
                "parent_id": None,
            }
        ),
    )

    assert state.fields["boolean"] is True
    assert state.fields["integer"] == 42
    assert state.fields["decimal"] == Decimal("10.25")
    assert state.fields["string"] == "value"
    assert state.fields["date"] == date(2026, 9, 8)
    assert state.fields["structured"] == StructuredValue({"nested": "value"})
    assert state.references["children"] == ()
    assert state.system_fields["deleted"] is False
    assert state.system_fields["version"] == 1


def test_runtime_durable_state_has_no_runtime_lifecycle_state() -> None:
    state = RuntimeDurableState.empty()

    assert not hasattr(state, "state")
    assert not hasattr(state, "context")


def test_runtime_durable_state_has_no_object_identity() -> None:
    state = RuntimeDurableState.empty()

    assert not hasattr(state, "identity")
    assert not hasattr(state, "object_type")
    assert not hasattr(state, "object_type_identity")


def test_repr_contains_four_components() -> None:
    state = RuntimeDurableState.empty()
    representation = repr(state)

    assert "fields=" in representation
    assert "references=" in representation
    assert "business_state=" in representation
    assert "system_fields=" in representation
