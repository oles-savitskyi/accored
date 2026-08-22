from __future__ import annotations

import pytest

from accore.platform.configuration import (
    ActiveConfiguration,
    ConfigurationIdentity,
    ConfigurationVersion,
    MetadataResolutionError,
    MetadataResolver,
    RuntimeConfigurationContext,
)
from accore.platform.foundation import Identifier
from accore.platform.metadata.catalog import CatalogMetadata
from accore.platform.metadata.registry import MetadataRegistry
from accore.platform.runtime.catalog import CatalogRuntime
from accore.platform.runtime.resolution import RuntimeResolver


def make_metadata(name: str) -> CatalogMetadata:
    identifier = Identifier.new()

    return CatalogMetadata(
        identifier=identifier,
        name=name,
        source_definition_id=identifier,
    )


def make_runtime_resolver(
    *metadata_objects: CatalogMetadata,
) -> tuple[RuntimeResolver, RuntimeConfigurationContext]:
    registry = MetadataRegistry()

    for metadata in metadata_objects:
        registry.register(metadata)

    configuration = ActiveConfiguration(
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(1),
        metadata_registry=registry,
    )

    context = RuntimeConfigurationContext(configuration)

    return RuntimeResolver(MetadataResolver()), context


def test_resolve_registered_metadata() -> None:
    metadata = make_metadata("Assortment")
    resolver, context = make_runtime_resolver(metadata)

    resolved = resolver.resolve(context, metadata.identifier)

    assert isinstance(resolved, CatalogRuntime)
    assert resolved.metadata is metadata


def test_resolve_unknown_metadata_fails() -> None:
    resolver, context = make_runtime_resolver()
    identifier = Identifier.new()

    with pytest.raises(MetadataResolutionError):
        resolver.resolve(context, identifier)


def test_resolve_multiple_metadata_objects() -> None:
    assortment = make_metadata("Assortment")
    employees = make_metadata("Employees")

    resolver, context = make_runtime_resolver(assortment, employees)

    assortment_runtime = resolver.resolve(context, assortment.identifier)
    employees_runtime = resolver.resolve(context, employees.identifier)

    assert assortment_runtime.metadata is assortment
    assert employees_runtime.metadata is employees


def test_resolution_does_not_modify_configuration_metadata() -> None:
    metadata = make_metadata("Assortment")

    registry = MetadataRegistry()
    registry.register(metadata)

    configuration = ActiveConfiguration(
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(1),
        metadata_registry=registry,
    )
    context = RuntimeConfigurationContext(configuration)

    resolver = RuntimeResolver(MetadataResolver())

    metadata_before = configuration.metadata_registry.get(metadata.identifier)

    resolved = resolver.resolve(context, metadata.identifier)

    assert resolved.metadata is metadata
    assert configuration.metadata_registry.get(metadata.identifier) is metadata_before


def test_resolution_uses_supplied_context() -> None:
    first = make_metadata("Assortment v1")
    second = make_metadata("Assortment v2")

    first_resolver, first_context = make_runtime_resolver(first)
    _, second_context = make_runtime_resolver(second)

    resolved = first_resolver.resolve(first_context, first.identifier)

    assert resolved.metadata is first

    with pytest.raises(MetadataResolutionError):
        first_resolver.resolve(second_context, first.identifier)


def test_runtime_resolver_uses_supplied_context() -> None:
    identifier = Identifier.new()

    first = make_metadata("Products v1")
    first = CatalogMetadata(
        identifier=identifier,
        name=first.name,
        source_definition_id=identifier,
    )

    second = CatalogMetadata(
        identifier=identifier,
        name="Products v2",
        source_definition_id=identifier,
    )

    resolver, first_context = make_runtime_resolver(first)
    _, second_context = make_runtime_resolver(second)

    assert resolver.resolve(first_context, identifier).metadata.name == "Products v1"
    assert resolver.resolve(second_context, identifier).metadata.name == "Products v2"
