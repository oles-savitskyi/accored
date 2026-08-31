from __future__ import annotations

import pytest

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
    ObjectLifecycleError,
    ObjectState,
)
from accore.platform.runtime import RuntimeResolver


def make_catalog_definition() -> CatalogDefinition:
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
    registry = MetadataRegistry()
    metadata = MetadataCompiler().compile(definition)
    registry.register(metadata)

    configuration = ActiveConfiguration(
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(1),
        published_metadata=registry.publish(),
    )

    return RuntimeConfigurationContext(configuration)


def make_object_instance() -> tuple[
    ObjectInstance,
    RuntimeConfigurationContext,
]:
    definition = make_catalog_definition()
    context = make_runtime_context(definition)

    runtime_resolver = RuntimeResolver(MetadataResolver())
    object_type = runtime_resolver.resolve(
        context,
        definition.identifier,
    )

    object_context = ObjectContext(runtime_context=context)
    instance = ObjectCreator.create(
        object_type=object_type,
        context=object_context,
    )

    return instance, context


def test_runtime_resolution_and_object_creation_form_one_boundary() -> None:
    instance, context = make_object_instance()

    assert isinstance(instance, ObjectInstance)
    assert instance.context.runtime_context is context
    assert instance.object_type.metadata.identifier == (
        context.configuration.published_metadata.get(
            instance.object_type.metadata.identifier
        ).identifier
    )
    assert instance.state is ObjectState.CREATED


def test_created_object_can_be_activated_and_disposed() -> None:
    instance, _ = make_object_instance()

    active_state = ObjectLifecycle.activate(instance.state)
    disposed_state = ObjectLifecycle.dispose(active_state)

    assert instance.state is ObjectState.CREATED
    assert active_state is ObjectState.ACTIVE
    assert disposed_state is ObjectState.DISPOSED


def test_object_identity_is_preserved_across_lifecycle_transitions() -> None:
    instance, _ = make_object_instance()
    identity = instance.identity

    active_state = ObjectLifecycle.activate(instance.state)
    disposed_state = ObjectLifecycle.dispose(active_state)

    assert instance.identity == identity
    assert disposed_state is ObjectState.DISPOSED


def test_object_context_preserves_runtime_configuration_context() -> None:
    instance, context = make_object_instance()

    assert instance.context.runtime_context is context
    assert instance.context.runtime_context.identity == ConfigurationIdentity("standard")
    assert instance.context.runtime_context.version == ConfigurationVersion(1)


def test_lifecycle_does_not_allow_invalid_transition_from_created_to_disposed() -> None:
    instance, _ = make_object_instance()

    with pytest.raises(
        ObjectLifecycleError,
        match="Cannot dispose object from state 'created'",
    ):
        ObjectLifecycle.dispose(instance.state)


def test_lifecycle_does_not_allow_activation_after_disposal() -> None:
    instance, _ = make_object_instance()

    active_state = ObjectLifecycle.activate(instance.state)
    disposed_state = ObjectLifecycle.dispose(active_state)

    with pytest.raises(
        ObjectLifecycleError,
        match="Cannot activate object from state 'disposed'",
    ):
        ObjectLifecycle.activate(disposed_state)


def test_object_creation_produces_independent_instances() -> None:
    definition = make_catalog_definition()
    context = make_runtime_context(definition)

    runtime_resolver = RuntimeResolver(MetadataResolver())
    object_type = runtime_resolver.resolve(
        context,
        definition.identifier,
    )

    object_context = ObjectContext(runtime_context=context)

    first = ObjectCreator.create(
        object_type=object_type,
        context=object_context,
    )
    second = ObjectCreator.create(
        object_type=object_type,
        context=object_context,
    )

    assert first is not second
    assert first.identity != second.identity
    assert first.object_type is second.object_type
    assert first.context is second.context
    assert first.state is ObjectState.CREATED
    assert second.state is ObjectState.CREATED
