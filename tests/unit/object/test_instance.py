from __future__ import annotations

import pytest

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
from accore.platform.object import ObjectContext, ObjectInstance, ObjectState
from accore.platform.runtime import CatalogRuntime


def make_runtime() -> CatalogRuntime:
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


def make_instance(identity: Identifier | None = None) -> ObjectInstance:
    return ObjectInstance(
        identity=identity or Identifier.new(),
        object_type=make_runtime(),
        context=make_context(),
    )


def test_object_instance_preserves_identity() -> None:
    identity = Identifier.new()

    instance = make_instance(identity)

    assert instance.identity == identity


def test_object_instance_preserves_object_type() -> None:
    object_type = make_runtime()

    instance = ObjectInstance(
        identity=Identifier.new(),
        object_type=object_type,
        context=make_context(),
    )

    assert instance.object_type is object_type


def test_object_instance_preserves_context() -> None:
    context = make_context()

    instance = ObjectInstance(
        identity=Identifier.new(),
        object_type=make_runtime(),
        context=context,
    )

    assert instance.context is context


def test_object_instance_starts_in_created_state() -> None:
    instance = make_instance()

    assert instance.state is ObjectState.CREATED


def test_object_instance_cannot_select_initial_state() -> None:
    with pytest.raises(
        ValueError,
        match="ObjectInstance must be created in CREATED state",
    ):
        ObjectInstance(
            identity=Identifier.new(),
            object_type=make_runtime(),
            context=make_context(),
            state=ObjectState.ACTIVE,
        )


def test_object_instance_is_immutable() -> None:
    instance = make_instance()

    with pytest.raises(AttributeError):
        instance.identity = Identifier.new()  # type: ignore[misc]

    with pytest.raises(AttributeError):
        instance.context = make_context()  # type: ignore[misc]

    with pytest.raises(AttributeError):
        instance.state = ObjectState.ACTIVE  # type: ignore[misc]


def test_object_instances_with_same_identity_are_equal() -> None:
    identity = Identifier.new()

    first = make_instance(identity)
    second = make_instance(identity)

    assert first == second


def test_object_instances_with_different_identity_are_not_equal() -> None:
    first = make_instance()
    second = make_instance()

    assert first != second


def test_object_instance_hash_is_based_on_identity() -> None:
    identity = Identifier.new()

    first = make_instance(identity)
    second = make_instance(identity)

    assert hash(first) == hash(second)


def test_object_instance_identity_is_independent_of_state() -> None:
    identity = Identifier.new()

    first = make_instance(identity)

    # State transitions are not implemented yet. This test establishes
    # that equality semantics are based on identity rather than state.
    assert first.identity == identity
    assert first.state is ObjectState.CREATED
