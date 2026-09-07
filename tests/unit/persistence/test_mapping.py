from __future__ import annotations

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
from accore.platform.persistence.mapping import (
    PersistentObjectHydrator,
    PersistentObjectMappingError,
)
from accore.platform.persistence.objects import (
    PersistentField,
    PersistentObject,
    PersistentObjectState,
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
        state=PersistentObjectState(),
    )

    runtime = PersistentObjectHydrator(resolver).hydrate(persistent, context)

    assert isinstance(runtime, ObjectInstance)
    assert runtime.identity == persistent.identity
    assert runtime.object_type.metadata_identity() == metadata.identifier
    assert runtime.context is context


def test_hydration_does_not_infer_runtime_state() -> None:
    metadata = make_metadata()
    context, resolver = make_context_and_resolver(metadata)
    persistent = PersistentObject(
        identity=Identifier.new(),
        object_type_identity=metadata.identifier,
        state=PersistentObjectState(),
    )

    runtime = PersistentObjectHydrator(resolver).hydrate(persistent, context)

    assert runtime.state.value == "created"


def test_hydration_rejects_unrepresentable_persistent_fields() -> None:
    metadata = make_metadata()
    context, resolver = make_context_and_resolver(metadata)
    persistent = PersistentObject(
        identity=Identifier.new(),
        object_type_identity=metadata.identifier,
        state=PersistentObjectState(fields=(PersistentField("name", "value"),)),
    )

    with pytest.raises(PersistentObjectMappingError):
        PersistentObjectHydrator(resolver).hydrate(persistent, context)


def test_hydration_rejects_unrepresentable_business_state() -> None:
    metadata = make_metadata()
    context, resolver = make_context_and_resolver(metadata)
    persistent = PersistentObject(
        identity=Identifier.new(),
        object_type_identity=metadata.identifier,
        state=PersistentObjectState(business_state="posted"),
    )

    with pytest.raises(PersistentObjectMappingError):
        PersistentObjectHydrator(resolver).hydrate(persistent, context)
