from __future__ import annotations

from accore.platform.configuration import (
    ActiveConfiguration,
    ConfigurationIdentity,
    ConfigurationVersion,
    MetadataResolver,
    RuntimeConfigurationContext,
)
from accore.platform.definitions import (
    AttributeDefinition,
    AttributeType,
    CatalogDefinition,
)
from accore.platform.foundation import Identifier
from accore.platform.metadata import MetadataCompiler
from accore.platform.metadata.registry import MetadataRegistry
from accore.platform.object import ObjectContext, ObjectCreator, ObjectInstance, ObjectState
from accore.platform.runtime import CatalogRuntime, RuntimeResolver


def make_definition() -> CatalogDefinition:
    return CatalogDefinition(
        identifier=Identifier.new(),
        name="Assortment",
        attributes=(
            AttributeDefinition(
                name="code",
                attribute_type=AttributeType.STRING,
                nullable=False,
                default_value="",
            ),
        ),
    )


def make_context(
    definition: CatalogDefinition,
) -> RuntimeConfigurationContext:
    metadata = MetadataCompiler().compile(definition)

    registry = MetadataRegistry()
    registry.register(metadata)

    configuration = ActiveConfiguration(
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(1),
        published_metadata=registry.publish(),
    )

    return RuntimeConfigurationContext(configuration)


def make_object_context(
    runtime_context: RuntimeConfigurationContext,
) -> ObjectContext:
    return ObjectContext(runtime_context=runtime_context)


def test_runtime_resolver_result_can_be_consumed_by_object_creator() -> None:
    definition = make_definition()
    context = make_context(definition)
    object_context = make_object_context(context)

    runtime = RuntimeResolver(MetadataResolver()).resolve(
        context,
        definition.identifier,
    )

    instance = ObjectCreator.create(
        object_type=runtime,
        context=object_context,
    )

    assert isinstance(runtime, CatalogRuntime)
    assert isinstance(instance, ObjectInstance)
    assert instance.object_type is runtime
    assert instance.context is object_context
    assert instance.state is ObjectState.CREATED


def test_runtime_resolver_and_object_creator_preserve_type_identity() -> None:
    definition = make_definition()
    context = make_context(definition)
    object_context = make_object_context(context)

    runtime = RuntimeResolver(MetadataResolver()).resolve(
        context,
        definition.identifier,
    )

    instance = ObjectCreator.create(
        object_type=runtime,
        context=object_context,
    )

    assert runtime.metadata.identifier == definition.identifier
    assert instance.object_type.metadata.identifier == definition.identifier


def test_object_creator_generates_instance_identity_independent_of_type_identity() -> None:
    definition = make_definition()
    context = make_context(definition)
    object_context = make_object_context(context)

    runtime = RuntimeResolver(MetadataResolver()).resolve(
        context,
        definition.identifier,
    )

    instance = ObjectCreator.create(
        object_type=runtime,
        context=object_context,
    )

    assert instance.identity != definition.identifier


def test_runtime_resolution_does_not_create_object_instance() -> None:
    definition = make_definition()
    context = make_context(definition)

    runtime = RuntimeResolver(MetadataResolver()).resolve(
        context,
        definition.identifier,
    )

    assert isinstance(runtime, CatalogRuntime)
    assert not isinstance(runtime, ObjectInstance)


def test_object_creation_does_not_resolve_runtime_type() -> None:
    definition = make_definition()
    context = make_context(definition)
    object_context = make_object_context(context)

    runtime = RuntimeResolver(MetadataResolver()).resolve(
        context,
        definition.identifier,
    )

    instance = ObjectCreator.create(
        object_type=runtime,
        context=object_context,
    )

    assert instance.object_type is runtime
