from __future__ import annotations

from accore.platform.object.context import ObjectContext
from accore.platform.object.instance import ObjectInstance
from accore.platform.persistence.objects import PersistentObject
from accore.platform.runtime.resolution import RuntimeResolver


class PersistentObjectMappingError(RuntimeError):
    """Raised when a persistent object cannot be mapped to runtime safely."""


class PersistentObjectHydrator:
    """Hydrate runtime object structure from a persistent object representation.

    Step 11 intentionally supports structural hydration only. Persistent field,
    business-state, and system-field materialization into Runtime are deferred
    until the Runtime Object Model exposes an explicit durable-state surface.
    """

    def __init__(self, runtime_resolver: RuntimeResolver) -> None:
        self._runtime_resolver = runtime_resolver

    def hydrate(
        self,
        persistent: PersistentObject,
        context: ObjectContext,
    ) -> ObjectInstance:
        """Hydrate a persistent object into a runtime object instance."""
        state = persistent.state
        if state.fields or state.system_fields or state.business_state is not None:
            raise PersistentObjectMappingError(
                "Persistent durable state cannot be hydrated into ObjectInstance "
                "because the current Runtime Object Model has no explicit durable "
                "state surface."
            )

        try:
            runtime_type = self._runtime_resolver.resolve(
                context.runtime_context,
                persistent.object_type_identity,
            )
        except (LookupError, TypeError) as exc:
            raise PersistentObjectMappingError(
                "Persistent object type cannot be resolved for runtime hydration."
            ) from exc

        if runtime_type.metadata_identity() != persistent.object_type_identity:
            raise PersistentObjectMappingError(
                "Resolved runtime object type identity does not match the "
                "persistent object type identity."
            )

        return ObjectInstance(
            identity=persistent.identity,
            object_type=runtime_type,
            context=context,
        )


__all__ = ["PersistentObjectHydrator", "PersistentObjectMappingError"]
