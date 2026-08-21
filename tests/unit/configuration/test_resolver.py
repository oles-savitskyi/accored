from __future__ import annotations

import pytest

from accore.platform.configuration import (
    ActiveConfiguration,
    ConfigurationIdentity,
    ConfigurationVersion,
    MetadataResolutionError,
    MetadataResolver,
    RuntimeConfigurationBinding,
    RuntimeConfigurationContext,
)
from accore.platform.definitions import CatalogDefinition
from accore.platform.foundation import Identifier
from accore.platform.metadata import MetadataCompiler, MetadataRegistry


def make_active_configuration(
    *,
    identity: str = "standard",
    version: int = 1,
    name: str = "Products",
    identifier: Identifier | None = None,
) -> tuple[ActiveConfiguration, Identifier]:
    metadata_identifier = identifier or Identifier.new()

    definition = CatalogDefinition(
        identifier=metadata_identifier,
        name=name,
    )

    metadata = MetadataCompiler().compile(definition)

    registry = MetadataRegistry()
    registry.register(metadata)

    configuration = ActiveConfiguration(
        identity=ConfigurationIdentity(identity),
        version=ConfigurationVersion(version),
        metadata_registry=registry,
    )

    return configuration, metadata_identifier


def make_context(
    configuration: ActiveConfiguration,
) -> RuntimeConfigurationContext:
    return RuntimeConfigurationContext(configuration=configuration)


def test_resolve_returns_metadata() -> None:
    configuration, identifier = make_active_configuration()
    context = make_context(configuration)

    resolver = MetadataResolver()

    metadata = resolver.resolve(context, identifier)

    assert metadata.name == "Products"


def test_resolve_uses_identifier() -> None:
    first, first_identifier = make_active_configuration(name="Products")
    second, second_identifier = make_active_configuration(name="Customers")

    resolver = MetadataResolver()

    first_context = make_context(first)
    second_context = make_context(second)

    assert resolver.resolve(first_context, first_identifier).name == "Products"
    assert resolver.resolve(second_context, second_identifier).name == "Customers"


def test_resolve_raises_when_metadata_missing() -> None:
    configuration, _ = make_active_configuration()
    context = make_context(configuration)

    resolver = MetadataResolver()
    missing_identifier = Identifier.new()

    with pytest.raises(MetadataResolutionError) as exc_info:
        resolver.resolve(context, missing_identifier)

    assert exc_info.value.identifier == missing_identifier


def test_resolve_uses_context_snapshot() -> None:
    binding = RuntimeConfigurationBinding()
    identifier = Identifier.new()

    first, _ = make_active_configuration(
        version=1,
        name="Products v1",
        identifier=identifier,
    )
    second, _ = make_active_configuration(
        version=2,
        name="Products v2",
        identifier=identifier,
    )

    binding.bind(first)
    first_context = binding.acquire()

    binding.bind(second)
    second_context = binding.acquire()

    resolver = MetadataResolver()

    assert resolver.resolve(first_context, identifier).name == "Products v1"
    assert resolver.resolve(second_context, identifier).name == "Products v2"


def test_resolver_does_not_retain_configuration() -> None:
    resolver = MetadataResolver()

    assert not hasattr(resolver, "_binding")
    assert not hasattr(resolver, "_configuration")


def test_resolve_does_not_mutate_configuration() -> None:
    configuration, identifier = make_active_configuration()
    registry_contents_before = configuration.metadata_registry.all()

    context = make_context(configuration)

    resolver = MetadataResolver()
    resolver.resolve(context, identifier)

    assert configuration.metadata_registry.all() == registry_contents_before


def test_resolved_metadata_identity_is_preserved() -> None:
    configuration, identifier = make_active_configuration()
    expected_metadata = configuration.metadata_registry.get(identifier)

    context = make_context(configuration)

    resolver = MetadataResolver()

    resolved_metadata = resolver.resolve(context, identifier)

    assert resolved_metadata is expected_metadata
