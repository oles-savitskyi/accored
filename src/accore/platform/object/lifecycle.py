from __future__ import annotations

from accore.platform.object.state import ObjectState


class ObjectLifecycleError(RuntimeError):
    """Raised when an object lifecycle transition is invalid."""


class ObjectLifecycle:
    """Manage lifecycle transitions for an object instance."""

    @staticmethod
    def activate(state: ObjectState) -> ObjectState:
        """Transition an object from CREATED to ACTIVE."""
        if state is not ObjectState.CREATED:
            raise ObjectLifecycleError(f"Cannot activate object from state '{state.value}'.")

        return ObjectState.ACTIVE

    @staticmethod
    def dispose(state: ObjectState) -> ObjectState:
        """Transition an object from ACTIVE to DISPOSED."""
        if state is not ObjectState.ACTIVE:
            raise ObjectLifecycleError(f"Cannot dispose object from state '{state.value}'.")

        return ObjectState.DISPOSED
