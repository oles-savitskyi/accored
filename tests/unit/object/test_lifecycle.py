import pytest

from accore.platform.object import ObjectLifecycle, ObjectLifecycleError, ObjectState


def test_created_can_transition_to_active() -> None:
    assert ObjectLifecycle.activate(ObjectState.CREATED) is ObjectState.ACTIVE


def test_active_can_transition_to_disposed() -> None:
    assert ObjectLifecycle.dispose(ObjectState.ACTIVE) is ObjectState.DISPOSED


def test_created_cannot_transition_directly_to_disposed() -> None:
    with pytest.raises(
        ObjectLifecycleError,
        match="Cannot dispose object from state 'created'",
    ):
        ObjectLifecycle.dispose(ObjectState.CREATED)


def test_active_cannot_be_activated_again() -> None:
    with pytest.raises(
        ObjectLifecycleError,
        match="Cannot activate object from state 'active'",
    ):
        ObjectLifecycle.activate(ObjectState.ACTIVE)


def test_created_cannot_be_activated_twice() -> None:
    with pytest.raises(
        ObjectLifecycleError,
        match="Cannot activate object from state 'active'",
    ):
        active_state = ObjectLifecycle.activate(ObjectState.CREATED)
        ObjectLifecycle.activate(active_state)


def test_disposed_object_cannot_be_activated() -> None:
    with pytest.raises(
        ObjectLifecycleError,
        match="Cannot activate object from state 'disposed'",
    ):
        ObjectLifecycle.activate(ObjectState.DISPOSED)


def test_disposed_object_cannot_be_disposed_again() -> None:
    with pytest.raises(
        ObjectLifecycleError,
        match="Cannot dispose object from state 'disposed'",
    ):
        ObjectLifecycle.dispose(ObjectState.DISPOSED)


def test_lifecycle_operations_do_not_mutate_input_state() -> None:
    state = ObjectState.CREATED

    active = ObjectLifecycle.activate(state)

    assert state is ObjectState.CREATED
    assert active is ObjectState.ACTIVE
