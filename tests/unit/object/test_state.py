from accore.platform.object.state import ObjectState


def test_object_states() -> None:
    assert [state.value for state in ObjectState] == [
        "created",
        "active",
        "disposed",
    ]


def test_object_states_are_distinct() -> None:
    assert ObjectState.CREATED is not ObjectState.ACTIVE
    assert ObjectState.ACTIVE is not ObjectState.DISPOSED
    assert ObjectState.CREATED is not ObjectState.DISPOSED


def test_object_state_values_are_canonical() -> None:
    assert ObjectState.CREATED.value == "created"
    assert ObjectState.ACTIVE.value == "active"
    assert ObjectState.DISPOSED.value == "disposed"
