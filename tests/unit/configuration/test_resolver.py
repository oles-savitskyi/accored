from __future__ import annotations

import pytest

from accore.platform.configuration import (
    ActiveConfiguration,
    ConfigurationIdentity,
    ConfigurationVersion,
    MetadataResolutionError,
    MetadataResolver,
    RuntimeConfigurationBinding,
)
from accore.platform.configuration.resolver import RuntimeConfigurationError
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


def test_resolve_returns_metadata() -> None:
    binding = RuntimeConfigurationBinding()
    configuration, identifier = make_active_configuration()

    binding.bind(configuration)

    resolver = MetadataResolver(binding)

    metadata = resolver.resolve(identifier)

    assert metadata.name == "Products"


def test_resolve_uses_identifier() -> None:
    binding = RuntimeConfigurationBinding()

    first, first_identifier = make_active_configuration(name="Products")
    second, second_identifier = make_active_configuration(name="Customers")

    binding.bind(first)
    resolver = MetadataResolver(binding)

    assert resolver.resolve(first_identifier).name == "Products"

    binding.bind(second)

    assert resolver.resolve(second_identifier).name == "Customers"


def test_resolve_raises_when_metadata_missing() -> None:
    binding = RuntimeConfigurationBinding()
    configuration, _ = make_active_configuration()

    binding.bind(configuration)
    resolver = MetadataResolver(binding)

    missing_identifier = Identifier.new()

    with pytest.raises(MetadataResolutionError) as exc_info:
        resolver.resolve(missing_identifier)

    assert exc_info.value.identifier == missing_identifier


def test_resolve_raises_when_configuration_not_bound() -> None:
    binding = RuntimeConfigurationBinding()
    resolver = MetadataResolver(binding)

    identifier = Identifier.new()

    with pytest.raises(RuntimeConfigurationError):
        resolver.resolve(identifier)


def test_resolve_uses_current_configuration() -> None:
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

    resolver = MetadataResolver(binding)

    binding.bind(first)
    assert resolver.resolve(identifier).name == "Products v1"

    binding.bind(second)
    assert resolver.resolve(identifier).name == "Products v2"


def test_resolver_does_not_keep_stale_configuration() -> None:
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

    resolver = MetadataResolver(binding)

    binding.bind(first)
    first_metadata = resolver.resolve(identifier)

    binding.bind(second)
    second_metadata = resolver.resolve(identifier)

    assert first_metadata.name == "Products v1"
    assert second_metadata.name == "Products v2"
    assert second_metadata is not first_metadata


def test_resolve_does_not_mutate_configuration() -> None:
    binding = RuntimeConfigurationBinding()
    configuration, identifier = make_active_configuration()

    registry_contents_before = configuration.metadata_registry.all()

    binding.bind(configuration)

    resolver = MetadataResolver(binding)
    resolver.resolve(identifier)

    assert configuration.metadata_registry.all() == registry_contents_before


def test_resolved_metadata_identity_is_preserved() -> None:
    binding = RuntimeConfigurationBinding()
    configuration, identifier = make_active_configuration()

    expected_metadata = configuration.metadata_registry.get(identifier)

    binding.bind(configuration)

    resolver = MetadataResolver(binding)

    resolved_metadata = resolver.resolve(identifier)

    assert resolved_metadata is expected_metadata
