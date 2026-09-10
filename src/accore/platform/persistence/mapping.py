from __future__ import annotations

from dataclasses import dataclass

from accore.platform.object.context import ObjectContext
from accore.platform.object.instance import ObjectInstance
from accore.platform.persistence.business_state import PersistentBusinessState
from accore.platform.persistence.field_state import PersistentFieldState
from accore.platform.persistence.objects import PersistentObject, PersistentObjectState
from accore.platform.persistence.reference_state import PersistentReferenceState
from accore.platform.persistence.system_field_state import PersistentSystemFieldState
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


class PersistentObjectMaterializationError(RuntimeError):
    """Raised when a runtime object cannot be materialized safely."""


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


class PersistentObjectMaterializer:
    """Materialize a runtime object and durable state into persistence."""

    def materialize(
        self,
        instance: ObjectInstance,
        durable_state: RuntimeDurableState,
    ) -> PersistentObject:
        """Create a persistent object from runtime-owned durable data."""
        try:
            return PersistentObject(
                identity=instance.identity,
                object_type_identity=instance.object_type.metadata_identity(),
                state=PersistentObjectState(
                    fields=PersistentFieldState(dict(durable_state.fields.items())),
                    references=PersistentReferenceState(dict(durable_state.references.items())),
                    business_state=PersistentBusinessState(
                        dict(durable_state.business_state.items())
                    ),
                    system_fields=PersistentSystemFieldState(
                        dict(durable_state.system_fields.items())
                    ),
                ),
            )
        except (TypeError, ValueError) as exc:
            raise PersistentObjectMaterializationError(
                "Runtime object cannot be materialized into a persistent object."
            ) from exc


__all__ = [
    "HydratedRuntimeObject",
    "PersistentObjectHydrator",
    "PersistentObjectMappingError",
    "PersistentObjectMaterializationError",
    "PersistentObjectMaterializer",
]
