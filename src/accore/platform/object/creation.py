from __future__ import annotations

from accore.platform.foundation import Identifier
from accore.platform.runtime import RuntimeObjectType

from .context import ObjectContext
from .instance import ObjectInstance


class ObjectCreationError(RuntimeError):
    """Raised when an object instance cannot be created."""


class ObjectCreator:
    """Create runtime object instances from resolved object types."""

    @staticmethod
    def create(
        object_type: RuntimeObjectType,
        context: ObjectContext,
    ) -> ObjectInstance:
        """Create a new object instance in the CREATED state."""
        try:
            identity = Identifier.new()
            return ObjectInstance(
                identity=identity,
                object_type=object_type,
                context=context,
            )
        except (TypeError, ValueError) as exc:
            raise ObjectCreationError("Failed to create object instance.") from exc
