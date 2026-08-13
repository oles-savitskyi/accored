import pytest

from accore.platform.foundation import Identifier
from accore.platform.metadata.catalog import CatalogMetadata
from accore.platform.metadata.registry import MetadataRegistry


def make_metadata(name: str) -> CatalogMetadata:
    identifier = Identifier.new()

    return CatalogMetadata(
        identifier=identifier,
        name=name,
        source_definition_id=identifier,
    )


def test_register_and_get() -> None:
    registry = MetadataRegistry()
    metadata = make_metadata("Assortment")

    registry.register(metadata)

    assert registry.get(metadata.identifier) is metadata


def test_contains_registered_metadata() -> None:
    registry = MetadataRegistry()
    metadata = make_metadata("Assortment")

    assert not registry.contains(metadata.identifier)

    registry.register(metadata)

    assert registry.contains(metadata.identifier)


def test_get_unknown_metadata_fails() -> None:
    registry = MetadataRegistry()
    identifier = Identifier.new()

    with pytest.raises(KeyError):
        registry.get(identifier)


def test_duplicate_registration_fails() -> None:
    registry = MetadataRegistry()
    metadata = make_metadata("Assortment")

    registry.register(metadata)

    conflicting = CatalogMetadata(
        identifier=metadata.identifier,
        name="Different Name",
        source_definition_id=metadata.source_definition_id,
    )

    with pytest.raises(KeyError):
        registry.register(conflicting)


def test_multiple_metadata_objects() -> None:
    registry = MetadataRegistry()

    first = make_metadata("Assortment")
    second = make_metadata("Employees")

    registry.register(first)
    registry.register(second)

    assert registry.get(first.identifier) is first
    assert registry.get(second.identifier) is second
    assert registry.contains(first.identifier)
    assert registry.contains(second.identifier)


def test_registered_metadata_remains_immutable() -> None:
    registry = MetadataRegistry()
    metadata = make_metadata("Assortment")

    registry.register(metadata)

    with pytest.raises(AttributeError):
        metadata.name = "Changed"  # type: ignore[misc]

    assert registry.get(metadata.identifier) is metadata
    assert registry.get(metadata.identifier).name == "Assortment"
