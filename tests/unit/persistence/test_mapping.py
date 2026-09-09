from __future__ import annotations

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
from accore.platform.object import ObjectContext
from accore.platform.persistence.business_state import PersistentBusinessState
from accore.platform.persistence.field_state import PersistentFieldState
from accore.platform.persistence.mapping import (
    HydratedRuntimeObject,
    PersistentObjectHydrator,
)
from accore.platform.persistence.objects import (
    PersistentObject,
    PersistentObjectState,
)
from accore.platform.persistence.reference_state import PersistentReferenceState
from accore.platform.persistence.system_field_state import (
    PersistentSystemFieldState,
)
from accore.platform.runtime import RuntimeResolver


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


def test_hydrate_preserves_identity_and_resolves_runtime_type() -> None:
    metadata = make_metadata()
    context, resolver = make_context_and_resolver(metadata)

    persistent = PersistentObject(
        identity=Identifier.new(),
        object_type_identity=metadata.identifier,
        state=PersistentObjectState(
            fields=PersistentFieldState({"name": "value"}),
            references=PersistentReferenceState(),
            business_state=PersistentBusinessState(),
            system_fields=PersistentSystemFieldState(),
        ),
    )

    hydrated = PersistentObjectHydrator(resolver).hydrate(
        persistent,
        context,
    )

    assert isinstance(hydrated, HydratedRuntimeObject)
    assert hydrated.instance.identity == persistent.identity
    assert hydrated.instance.object_type.metadata_identity() == persistent.object_type_identity
    assert hydrated.instance.context is context


def test_hydration_does_not_restore_runtime_lifecycle_state() -> None:
    metadata = make_metadata()
    context, resolver = make_context_and_resolver(metadata)

    persistent = PersistentObject(
        identity=Identifier.new(),
        object_type_identity=metadata.identifier,
        state=PersistentObjectState(
            fields=PersistentFieldState({}),
            references=PersistentReferenceState({}),
            business_state=PersistentBusinessState({}),
            system_fields=PersistentSystemFieldState({}),
        ),
    )

    hydrated = PersistentObjectHydrator(resolver).hydrate(
        persistent,
        context,
    )

    assert hydrated.instance.state.value == "created"


def test_hydrate_preserves_all_durable_state() -> None:
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
                    "children": (
                        Identifier.new(),
                        Identifier.new(),
                    ),
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
                }
            ),
        ),
    )

    hydrated = PersistentObjectHydrator(resolver).hydrate(
        persistent,
        context,
    )

    assert hydrated.durable_state.fields["name"] == "value"
    assert hydrated.durable_state.fields["optional"] is None

    assert hydrated.durable_state.references["parent"] == parent_identity
    assert len(hydrated.durable_state.references["children"]) == 2

    assert hydrated.durable_state.business_state[business_definition] == business_value

    assert hydrated.durable_state.system_fields["parent_id"] == parent_identity
    assert hydrated.durable_state.system_fields["version"] == 7
    assert hydrated.durable_state.system_fields["deleted"] is False
