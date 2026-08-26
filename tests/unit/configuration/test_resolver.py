from __future__ import annotations

import pytest

from accore.platform.configuration import (
    ActiveConfiguration,
    ConfigurationActivator,
    ConfigurationCandidate,
    ConfigurationIdentity,
    ConfigurationValidator,
    ConfigurationVersion,
    MetadataResolutionError,
    MetadataResolver,
    RuntimeConfigurationBinding,
    RuntimeConfigurationContext,
)
from accore.platform.definitions import CatalogDefinition
from accore.platform.foundation import Identifier
from accore.platform.metadata import MetadataCompiler, MetadataRegistry


def make_validated_candidate(
    *,
    identity: str = "standard",
    version: int = 1,
    name: str = "Products",
    identifier: Identifier | None = None,
) -> ConfigurationCandidate:
    metadata_identifier = identifier or Identifier.new()

    definition = CatalogDefinition(
        identifier=metadata_identifier,
        name=name,
    )

    metadata = MetadataCompiler().compile(definition)

    registry = MetadataRegistry()
    registry.register(metadata)

    candidate = ConfigurationCandidate(
        identity=ConfigurationIdentity(identity),
        version=ConfigurationVersion(version),
        metadata_registry=registry,
    )

    ConfigurationValidator().validate(candidate)

    return candidate


def make_active_configuration(
    *,
    identity: str = "standard",
    version: int = 1,
    name: str = "Products",
    identifier: Identifier | None = None,
) -> tuple[ActiveConfiguration, Identifier]:
    candidate = make_validated_candidate(
        identity=identity,
        version=version,
        name=name,
        identifier=identifier,
    )

    metadata_identifier = candidate.metadata_registry.all()[0].identifier

    configuration = ConfigurationActivator().activate(candidate)

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
    published_contents_before = configuration.published_metadata.all()

    context = make_context(configuration)

    resolver = MetadataResolver()
    resolver.resolve(context, identifier)

    assert configuration.published_metadata.all() == published_contents_before


def test_resolved_metadata_identity_is_preserved() -> None:
    configuration, identifier = make_active_configuration()
    expected_metadata = configuration.published_metadata.get(identifier)

    context = make_context(configuration)

    resolver = MetadataResolver()

    resolved_metadata = resolver.resolve(context, identifier)

    assert resolved_metadata is expected_metadata


def test_metadata_resolver_uses_published_metadata_snapshot() -> None:
    configuration, identifier = make_active_configuration()

    binding = RuntimeConfigurationBinding()
    binding.bind(configuration)

    context = binding.acquire()
    resolver = MetadataResolver()

    resolved = resolver.resolve(context, identifier)

    assert resolved is configuration.published_metadata.get(identifier)


def test_metadata_resolver_does_not_see_metadata_added_after_activation() -> None:
    candidate = make_validated_candidate()

    active = ConfigurationActivator().activate(candidate)

    binding = RuntimeConfigurationBinding()
    binding.bind(active)

    context = binding.acquire()

    extra_identifier = Identifier.new()
    extra_metadata = MetadataCompiler().compile(
        CatalogDefinition(
            identifier=extra_identifier,
            name="Later Catalog",
        )
    )

    candidate.metadata_registry.register(extra_metadata)

    resolver = MetadataResolver()

    with pytest.raises(MetadataResolutionError):
        resolver.resolve(context, extra_identifier)

    assert not active.published_metadata.contains(extra_identifier)
