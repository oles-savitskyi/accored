from enum import Enum


class ObjectState(str, Enum):
    """Lifecycle states of an object instance."""

    CREATED = "created"
    ACTIVE = "active"
    DISPOSED = "disposed"
