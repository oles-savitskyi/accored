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
from accore.platform.object import (
    ObjectContext,
    ObjectCreator,
    ObjectInstance,
    ObjectLifecycle,
    ObjectState,
)
from accore.platform.runtime import CatalogRuntime, RuntimeResolver


def make_assortment_definition() -> CatalogDefinition:
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


def make_runtime_context(
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


def test_assortment_metadata_resolves_to_catalog_runtime() -> None:
    definition = make_assortment_definition()
    context = make_runtime_context(definition)

    metadata_resolver = MetadataResolver()
    runtime_resolver = RuntimeResolver(metadata_resolver)

    runtime_type = runtime_resolver.resolve(
        context=context,
        identifier=definition.identifier,
    )

    assert isinstance(runtime_type, CatalogRuntime)
    assert runtime_type.metadata.identifier == definition.identifier
    assert runtime_type.metadata.name == "Assortment"


def test_resolved_assortment_runtime_type_creates_object_instance() -> None:
    definition = make_assortment_definition()
    context = make_runtime_context(definition)

    metadata_resolver = MetadataResolver()
    runtime_resolver = RuntimeResolver(metadata_resolver)

    runtime_type = runtime_resolver.resolve(
        context=context,
        identifier=definition.identifier,
    )

    object_context = ObjectContext(runtime_context=context)

    instance = ObjectCreator.create(
        object_type=runtime_type,
        context=object_context,
    )

    assert isinstance(instance, ObjectInstance)
    assert instance.object_type is runtime_type
    assert instance.context is object_context
    assert isinstance(instance.identity, Identifier)
    assert instance.state is ObjectState.CREATED


def test_assortment_object_instance_has_independent_identity() -> None:
    definition = make_assortment_definition()
    context = make_runtime_context(definition)

    metadata_resolver = MetadataResolver()
    runtime_resolver = RuntimeResolver(metadata_resolver)

    runtime_type = runtime_resolver.resolve(
        context=context,
        identifier=definition.identifier,
    )

    object_context = ObjectContext(runtime_context=context)

    first = ObjectCreator.create(
        object_type=runtime_type,
        context=object_context,
    )
    second = ObjectCreator.create(
        object_type=runtime_type,
        context=object_context,
    )

    assert first.object_type is runtime_type
    assert second.object_type is runtime_type
    assert first.identity != second.identity
    assert first != second


def test_assortment_object_instance_uses_explicit_runtime_context() -> None:
    definition = make_assortment_definition()
    context = make_runtime_context(definition)

    metadata_resolver = MetadataResolver()
    runtime_resolver = RuntimeResolver(metadata_resolver)

    runtime_type = runtime_resolver.resolve(
        context=context,
        identifier=definition.identifier,
    )

    object_context = ObjectContext(runtime_context=context)

    instance = ObjectCreator.create(
        object_type=runtime_type,
        context=object_context,
    )

    assert instance.context.runtime_context is context
    assert instance.context.runtime_context.configuration.identity == ConfigurationIdentity(
        "standard"
    )
    assert instance.context.runtime_context.configuration.version == ConfigurationVersion(1)


def test_assortment_object_instance_lifecycle_is_generic() -> None:
    definition = make_assortment_definition()
    context = make_runtime_context(definition)

    metadata_resolver = MetadataResolver()
    runtime_resolver = RuntimeResolver(metadata_resolver)

    runtime_type = runtime_resolver.resolve(
        context=context,
        identifier=definition.identifier,
    )

    object_context = ObjectContext(runtime_context=context)

    instance = ObjectCreator.create(
        object_type=runtime_type,
        context=object_context,
    )

    assert instance.state is ObjectState.CREATED

    active_state = ObjectLifecycle.activate(instance.state)

    assert active_state is ObjectState.ACTIVE
