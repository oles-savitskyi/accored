from __future__ import annotations

from dataclasses import dataclass

from accore.platform.object.context import ObjectContext
from accore.platform.object.instance import ObjectInstance
from accore.platform.persistence.objects import PersistentObject
from accore.platform.runtime.business_state import BusinessStateSnapshot
from accore.platform.runtime.durable_field_state import DurableFieldState
from accore.platform.runtime.durable_reference_state import DurableReferenceState
from accore.platform.runtime.durable_state import RuntimeDurableState
from accore.platform.runtime.durable_system_field_state import (
    DurableSystemFieldState,
)
from accore.platform.runtime.resolution import RuntimeResolver


class PersistentObjectMappingError(RuntimeError):
    """Raised when a persistent object cannot be mapped to runtime safely."""


@dataclass(frozen=True, slots=True)
class HydratedRuntimeObject:
    """Runtime object instance together with its durable runtime state."""

    instance: ObjectInstance
    durable_state: RuntimeDurableState


class PersistentObjectHydrator:
    """Hydrate runtime object structure and durable state from persistence."""

    def __init__(self, runtime_resolver: RuntimeResolver) -> None:
        self._runtime_resolver = runtime_resolver

    def hydrate(
        self,
        persistent: PersistentObject,
        context: ObjectContext,
    ) -> HydratedRuntimeObject:
        """Hydrate a persistent object into runtime representations."""
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

        instance = ObjectInstance(
            identity=persistent.identity,
            object_type=runtime_type,
            context=context,
        )

        durable_state = RuntimeDurableState(
            fields=DurableFieldState(dict(persistent.state.fields.items())),
            references=DurableReferenceState(dict(persistent.state.references.items())),
            business_state=BusinessStateSnapshot(dict(persistent.state.business_state.items())),
            system_fields=DurableSystemFieldState(dict(persistent.state.system_fields.items())),
        )

        return HydratedRuntimeObject(
            instance=instance,
            durable_state=durable_state,
        )


__all__ = [
    "HydratedRuntimeObject",
    "PersistentObjectHydrator",
    "PersistentObjectMappingError",
]
