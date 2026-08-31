from __future__ import annotations

from accore.platform.configuration import (
    ActiveConfiguration,
    ConfigurationIdentity,
    ConfigurationVersion,
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
from accore.platform.runtime import CatalogRuntime, RuntimeObjectType


def make_runtime() -> RuntimeObjectType:
    definition = CatalogDefinition(
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

    metadata = MetadataCompiler().compile(definition)

    return CatalogRuntime(metadata=metadata)


def make_context() -> ObjectContext:
    registry = MetadataRegistry()
    configuration = ActiveConfiguration(
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(1),
        published_metadata=registry.publish(),
    )
    runtime_context = RuntimeConfigurationContext(configuration)

    return ObjectContext(runtime_context=runtime_context)


def test_creator_creates_object_instance() -> None:
    instance = ObjectCreator.create(
        object_type=make_runtime(),
        context=make_context(),
    )

    assert isinstance(instance, ObjectInstance)


def test_creator_generates_object_identity() -> None:
    instance = ObjectCreator.create(
        object_type=make_runtime(),
        context=make_context(),
    )

    assert isinstance(instance.identity, Identifier)


def test_creator_generates_unique_identity_per_instance() -> None:
    object_type = make_runtime()
    context = make_context()

    first = ObjectCreator.create(
        object_type=object_type,
        context=context,
    )
    second = ObjectCreator.create(
        object_type=object_type,
        context=context,
    )

    assert first.identity != second.identity


def test_creator_preserves_object_type() -> None:
    object_type = make_runtime()

    instance = ObjectCreator.create(
        object_type=object_type,
        context=make_context(),
    )

    assert instance.object_type is object_type


def test_creator_preserves_context() -> None:
    context = make_context()

    instance = ObjectCreator.create(
        object_type=make_runtime(),
        context=context,
    )

    assert instance.context is context


def test_creator_initializes_created_state() -> None:
    instance = ObjectCreator.create(
        object_type=make_runtime(),
        context=make_context(),
    )

    assert instance.state is ObjectState.CREATED


def test_creator_does_not_perform_lifecycle_transition() -> None:
    instance = ObjectCreator.create(
        object_type=make_runtime(),
        context=make_context(),
    )

    assert instance.state is ObjectState.CREATED


def test_creator_does_not_share_identity_between_instances() -> None:
    object_type = make_runtime()
    context = make_context()

    first = ObjectCreator.create(
        object_type=object_type,
        context=context,
    )
    second = ObjectCreator.create(
        object_type=object_type,
        context=context,
    )

    assert first is not second
    assert first.identity != second.identity
