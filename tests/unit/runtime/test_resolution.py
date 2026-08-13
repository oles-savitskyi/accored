import pytest

from accore.platform.foundation import Identifier
from accore.platform.metadata.catalog import CatalogMetadata
from accore.platform.metadata.registry import MetadataRegistry
from accore.platform.runtime.resolution import RuntimeResolver


def make_metadata(name: str) -> CatalogMetadata:
    identifier = Identifier.new()

    return CatalogMetadata(
        identifier=identifier,
        name=name,
        source_definition_id=identifier,
    )


def test_resolve_registered_metadata() -> None:
    registry = MetadataRegistry()
    metadata = make_metadata("Assortment")

    registry.register(metadata)

    resolver = RuntimeResolver(registry)

    resolved = resolver.resolve(metadata.identifier)

    assert resolved is metadata


def test_resolve_unknown_metadata_fails() -> None:
    registry = MetadataRegistry()
    resolver = RuntimeResolver(registry)

    identifier = Identifier.new()

    with pytest.raises(KeyError):
        resolver.resolve(identifier)


def test_resolve_multiple_metadata_objects() -> None:
    registry = MetadataRegistry()

    assortment = make_metadata("Assortment")
    employees = make_metadata("Employees")

    registry.register(assortment)
    registry.register(employees)

    resolver = RuntimeResolver(registry)

    assert resolver.resolve(assortment.identifier) is assortment
    assert resolver.resolve(employees.identifier) is employees


def test_resolution_does_not_modify_registry() -> None:
    registry = MetadataRegistry()
    metadata = make_metadata("Assortment")

    registry.register(metadata)

    resolver = RuntimeResolver(registry)

    resolved = resolver.resolve(metadata.identifier)

    assert resolved is metadata
    assert registry.contains(metadata.identifier)
    assert registry.get(metadata.identifier) is metadata
