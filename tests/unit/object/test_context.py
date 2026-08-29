import pytest

from accore.platform.configuration import (
    ActiveConfiguration,
    ConfigurationIdentity,
    ConfigurationVersion,
    RuntimeConfigurationContext,
)
from accore.platform.foundation import Identifier
from accore.platform.metadata.registry import MetadataRegistry
from accore.platform.object import ObjectContext


def make_runtime_context() -> RuntimeConfigurationContext:
    registry = MetadataRegistry()

    configuration = ActiveConfiguration(
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(1),
        published_metadata=registry.publish(),
    )

    return RuntimeConfigurationContext(configuration)


def test_object_context_preserves_runtime_configuration_context() -> None:
    runtime_context = make_runtime_context()

    context = ObjectContext(
        runtime_configuration_context=runtime_context,
    )

    assert context.runtime_configuration_context is runtime_context


def test_object_context_is_immutable() -> None:
    context = ObjectContext(
        runtime_configuration_context=make_runtime_context(),
    )

    with pytest.raises(AttributeError):
        context.runtime_configuration_context = make_runtime_context()  # type: ignore[misc]


def test_object_context_can_reference_different_runtime_snapshots() -> None:
    first_configuration = ActiveConfiguration(
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(1),
        published_metadata=MetadataRegistry().publish(),
    )
    second_configuration = ActiveConfiguration(
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(2),
        published_metadata=MetadataRegistry().publish(),
    )

    first_runtime_context = RuntimeConfigurationContext(first_configuration)
    second_runtime_context = RuntimeConfigurationContext(second_configuration)

    first_context = ObjectContext(
        runtime_configuration_context=first_runtime_context,
    )
    second_context = ObjectContext(
        runtime_configuration_context=second_runtime_context,
    )

    assert first_context.runtime_configuration_context is first_runtime_context
    assert second_context.runtime_configuration_context is second_runtime_context
    assert first_context != second_context


def test_object_context_does_not_define_object_identity() -> None:
    context = ObjectContext(
        runtime_configuration_context=make_runtime_context(),
    )

    assert not hasattr(context, "identity")
    assert Identifier.new() != Identifier.new()
