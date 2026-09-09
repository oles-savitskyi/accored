from __future__ import annotations

from dataclasses import dataclass

from accore.platform.runtime.business_state import BusinessStateSnapshot
from accore.platform.runtime.durable_field_state import DurableFieldState
from accore.platform.runtime.durable_reference_state import DurableReferenceState
from accore.platform.runtime.durable_system_field_state import (
    DurableSystemFieldState,
)


@dataclass(frozen=True, slots=True)
class RuntimeDurableState:
    """Immutable runtime representation of an object's durable state.

    RuntimeDurableState is the semantic composition of the four durable
    state domains:

    * user/domain fields;
    * object references;
    * business state;
    * durable system fields.

    The model intentionally does not contain runtime lifecycle state,
    runtime context, persistence objects, storage handles, or object
    orchestration.

    Object identity remains structural identity of ObjectInstance and is
    associated with this state externally.
    """

    fields: DurableFieldState
    references: DurableReferenceState
    business_state: BusinessStateSnapshot
    system_fields: DurableSystemFieldState

    @classmethod
    def empty(cls) -> RuntimeDurableState:
        """Create an empty runtime durable state."""
        return cls(
            fields=DurableFieldState.empty(),
            references=DurableReferenceState.empty(),
            business_state=BusinessStateSnapshot.empty(),
            system_fields=DurableSystemFieldState.empty(),
        )
