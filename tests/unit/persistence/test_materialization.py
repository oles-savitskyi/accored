from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

from accore.platform.configuration import (
    ActiveConfiguration,
    ConfigurationIdentity,
    ConfigurationVersion,
    MetadataResolver,
    RuntimeConfigurationContext,
)
from accore.platform.foundation import Identifier
from accore.platform.metadata.catalog import CatalogMetadata
from accore.platform.metadata.registry import MetadataRegistry
from accore.platform.object import ObjectContext, ObjectInstance
from accore.platform.persistence import (
    PersistentObject,
    PersistentObjectMaterializationError,
    PersistentObjectMaterializer,
    PersistentObjectState,
)
from accore.platform.persistence.business_state import PersistentBusinessState
from accore.platform.persistence.field_state import PersistentFieldState
from accore.platform.persistence.mapping import PersistentObjectHydrator
from accore.platform.persistence.reference_state import PersistentReferenceState
from accore.platform.persistence.system_field_state import (
    PersistentSystemFieldState,
)
from accore.platform.runtime import RuntimeResolver
from accore.platform.runtime.business_state import BusinessStateSnapshot
from accore.platform.runtime.durable_field_state import DurableFieldState
from accore.platform.runtime.durable_reference_state import DurableReferenceState
from accore.platform.runtime.durable_state import RuntimeDurableState
from accore.platform.runtime.durable_system_field_state import (
    DurableSystemFieldState,
)


def make_context_and_resolver(
    metadata: CatalogMetadata,
) -> tuple[ObjectContext, RuntimeResolver]:
    registry = MetadataRegistry()
    registry.register(metadata)
    configuration = ActiveConfiguration(
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(1),
        published_metadata=registry.publish(),
    )
    runtime_context = RuntimeConfigurationContext(configuration)
    return ObjectContext(runtime_context), RuntimeResolver(MetadataResolver())


def make_metadata() -> CatalogMetadata:
    identifier = Identifier.new()
    return CatalogMetadata(
        identifier=identifier,
        name="Assortment",
        source_definition_id=identifier,
    )


def make_instance() -> tuple[ObjectInstance, ObjectContext, RuntimeResolver]:
    metadata = make_metadata()
    context, resolver = make_context_and_resolver(metadata)
    runtime_type = resolver.resolve(context.runtime_context, metadata.identifier)
    instance = ObjectInstance(
        identity=Identifier.new(),
        object_type=runtime_type,
        context=context,
    )
    return instance, context, resolver


def make_durable_state() -> RuntimeDurableState:
    parent_identity = Identifier.new()
    child_one = Identifier.new()
    child_two = Identifier.new()
    business_definition = Identifier.new()
    business_value = Identifier.new()

    return RuntimeDurableState(
        fields=DurableFieldState(
            {
                "name": "value",
                "optional": None,
            }
        ),
        references=DurableReferenceState(
            {
                "parent": parent_identity,
                "children": (child_one, child_two),
                "nullable": None,
            }
        ),
        business_state=BusinessStateSnapshot(
            {
                business_definition: business_value,
            }
        ),
        system_fields=DurableSystemFieldState(
            {
                "parent_id": parent_identity,
                "version": 7,
                "deleted": False,
                "nullable": None,
            }
        ),
    )


def test_materializer_is_available_from_public_persistence_api() -> None:
    materializer = PersistentObjectMaterializer()

    assert materializer is not None
    assert issubclass(PersistentObjectMaterializationError, RuntimeError)


def test_materialize_preserves_object_identity() -> None:
    instance, _, _ = make_instance()
    durable_state = RuntimeDurableState.empty()

    result = PersistentObjectMaterializer().materialize(instance, durable_state)

    assert result.identity == instance.identity


def test_materialize_uses_runtime_object_type_metadata_identity() -> None:
    instance, _, _ = make_instance()
    durable_state = RuntimeDurableState.empty()

    result = PersistentObjectMaterializer().materialize(instance, durable_state)

    assert result.object_type_identity == instance.object_type.metadata_identity()


def test_materialize_preserves_all_durable_state_domains() -> None:
    instance, _, _ = make_instance()
    durable_state = make_durable_state()

    result = PersistentObjectMaterializer().materialize(instance, durable_state)

    assert result.state.fields == PersistentFieldState(dict(durable_state.fields.items()))
    assert result.state.references == PersistentReferenceState(
        dict(durable_state.references.items())
    )
    assert result.state.business_state == PersistentBusinessState(
        dict(durable_state.business_state.items())
    )
    assert result.state.system_fields == PersistentSystemFieldState(
        dict(durable_state.system_fields.items())
    )


def test_materialize_preserves_missing_and_explicit_null() -> None:
    instance, _, _ = make_instance()
    durable_state = RuntimeDurableState(
        fields=DurableFieldState({"null": None, "value": "present"}),
        references=DurableReferenceState({"null": None}),
        business_state=BusinessStateSnapshot.empty(),
        system_fields=DurableSystemFieldState({"null": None}),
    )

    result = PersistentObjectMaterializer().materialize(instance, durable_state)

    assert "missing" not in result.state.fields
    assert result.state.fields["null"] is None
    assert result.state.fields["value"] == "present"

    assert "missing" not in result.state.references
    assert result.state.references["null"] is None

    assert "missing" not in result.state.system_fields
    assert result.state.system_fields["null"] is None


def test_materialize_preserves_reference_identity_without_graph_traversal() -> None:
    instance, _, _ = make_instance()
    parent_identity = Identifier.new()
    children = (Identifier.new(), Identifier.new())
    durable_state = RuntimeDurableState(
        fields=DurableFieldState.empty(),
        references=DurableReferenceState(
            {
                "parent": parent_identity,
                "children": children,
            }
        ),
        business_state=BusinessStateSnapshot.empty(),
        system_fields=DurableSystemFieldState.empty(),
    )

    result = PersistentObjectMaterializer().materialize(instance, durable_state)

    assert result.state.references["parent"] == parent_identity
    assert result.state.references["children"] == children


def test_materialize_does_not_persist_runtime_lifecycle_state() -> None:
    instance, _, _ = make_instance()
    durable_state = RuntimeDurableState.empty()

    result = PersistentObjectMaterializer().materialize(instance, durable_state)

    assert not hasattr(result.state, "lifecycle")
    assert instance.state.value == "created"


def test_materialize_does_not_persist_runtime_context() -> None:
    instance, _, _ = make_instance()
    durable_state = RuntimeDurableState.empty()

    result = PersistentObjectMaterializer().materialize(instance, durable_state)

    assert not hasattr(result, "context")
    assert not hasattr(result.state, "context")


def test_materialize_does_not_persist_arbitrary_runtime_attributes() -> None:
    instance, _, _ = make_instance()
    durable_state = RuntimeDurableState(
        fields=DurableFieldState({"name": "durable"}),
        references=DurableReferenceState.empty(),
        business_state=BusinessStateSnapshot.empty(),
        system_fields=DurableSystemFieldState.empty(),
    )

    result = PersistentObjectMaterializer().materialize(instance, durable_state)

    assert result.state.fields["name"] == "durable"
    assert "runtime_only" not in result.state.fields
    assert "runtime_only" not in result.state.system_fields


def test_materialize_translates_invalid_durable_representation() -> None:
    instance, _, _ = make_instance()
    invalid_state = cast(
        RuntimeDurableState,
        SimpleNamespace(
            fields=SimpleNamespace(items=lambda: {"invalid": object()}.items()),
            references=DurableReferenceState.empty(),
            business_state=BusinessStateSnapshot.empty(),
            system_fields=DurableSystemFieldState.empty(),
        ),
    )

    with pytest.raises(PersistentObjectMaterializationError):
        PersistentObjectMaterializer().materialize(instance, invalid_state)


def test_hydration_materialization_preserves_persistent_semantics() -> None:
    metadata = make_metadata()
    context, resolver = make_context_and_resolver(metadata)
    parent_identity = Identifier.new()
    business_definition = Identifier.new()
    business_value = Identifier.new()

    persistent = PersistentObject(
        identity=Identifier.new(),
        object_type_identity=metadata.identifier,
        state=PersistentObjectState(
            fields=PersistentFieldState(
                {
                    "name": "value",
                    "optional": None,
                }
            ),
            references=PersistentReferenceState(
                {
                    "parent": parent_identity,
                    "children": (Identifier.new(), Identifier.new()),
                    "nullable": None,
                }
            ),
            business_state=PersistentBusinessState(
                {
                    business_definition: business_value,
                }
            ),
            system_fields=PersistentSystemFieldState(
                {
                    "parent_id": parent_identity,
                    "version": 7,
                    "deleted": False,
                    "nullable": None,
                }
            ),
        ),
    )

    hydrated = PersistentObjectHydrator(resolver).hydrate(
        persistent,
        context,
    )
    rematerialized = PersistentObjectMaterializer().materialize(
        hydrated.instance,
        hydrated.durable_state,
    )

    assert rematerialized.identity == persistent.identity
    assert rematerialized.object_type_identity == persistent.object_type_identity
    assert rematerialized.state.fields == persistent.state.fields
    assert rematerialized.state.references == persistent.state.references
    assert rematerialized.state.business_state == persistent.state.business_state
    assert rematerialized.state.system_fields == persistent.state.system_fields
