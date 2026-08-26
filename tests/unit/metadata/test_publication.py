import pytest

from accore.platform.foundation import Identifier
from accore.platform.metadata import (
    CatalogMetadata,
    MetadataRegistry,
    PublishedMetadataView,
)


def make_metadata(name: str) -> CatalogMetadata:
    identifier = Identifier("01ARZ3NDEKTSV4RRFFQ69G5FAV")

    return CatalogMetadata(
        identifier=identifier,
        name=name,
        source_definition_id=identifier,
    )


def test_publish_creates_read_only_snapshot() -> None:
    registry = MetadataRegistry()
    metadata_v1 = make_metadata("Catalog v1")

    registry.register(metadata_v1)

    published = registry.publish()

    assert isinstance(published, PublishedMetadataView)
    assert published.get(metadata_v1.identifier) is metadata_v1
    assert published.contains(metadata_v1.identifier)
    assert published.all() == (metadata_v1,)


def test_published_view_is_snapshot_of_registry_at_publication_time() -> None:
    registry = MetadataRegistry()

    metadata_v1 = make_metadata("Catalog v1")
    registry.register(metadata_v1)

    published = registry.publish()

    other_identifier = Identifier("01ARZ3NDEKTSV4RRFFQ69G5FAW")
    metadata_v2 = CatalogMetadata(
        identifier=other_identifier,
        name="Catalog v2",
        source_definition_id=other_identifier,
    )

    registry.register(metadata_v2)

    assert published.contains(metadata_v1.identifier)
    assert not published.contains(other_identifier)
    assert published.all() == (metadata_v1,)


def test_published_view_does_not_expose_mutation_api() -> None:
    registry = MetadataRegistry()
    metadata = make_metadata("Catalog")

    registry.register(metadata)
    published = registry.publish()

    assert not hasattr(published, "register")
    assert not hasattr(published, "publish")


def test_published_view_returns_tuple_from_all() -> None:
    registry = MetadataRegistry()
    metadata = make_metadata("Catalog")

    registry.register(metadata)
    published = registry.publish()

    result = published.all()

    assert isinstance(result, tuple)

    with pytest.raises(AttributeError):
        result.append(metadata)  # type: ignore[attr-defined]


def test_published_view_missing_metadata_raises_key_error() -> None:
    registry = MetadataRegistry()
    published = registry.publish()

    missing_identifier = Identifier("01ARZ3NDEKTSV4RRFFQ69G5FAW")

    with pytest.raises(KeyError, match="Metadata not found"):
        published.get(missing_identifier)
