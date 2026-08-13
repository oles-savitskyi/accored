import pytest

from accore.platform.foundation import Identifier
from accore.platform.metadata.base import Metadata, MetadataType


def test_valid_metadata() -> None:
    metadata = Metadata(
        identifier=Identifier.new(),
        metadata_type=MetadataType.CATALOG,
        name="Assortment",
        source_definition_id=Identifier.new(),
    )

    assert metadata.name == "Assortment"
    assert metadata.metadata_type is MetadataType.CATALOG
    assert metadata.normalized_content == ()


def test_metadata_identity_is_preserved() -> None:
    metadata_id = Identifier.new()
    source_definition_id = Identifier.new()

    metadata = Metadata(
        identifier=metadata_id,
        metadata_type=MetadataType.CATALOG,
        name="Assortment",
        source_definition_id=source_definition_id,
    )

    assert metadata.identifier == metadata_id
    assert metadata.source_definition_id == source_definition_id


def test_metadata_is_immutable() -> None:
    metadata = Metadata(
        identifier=Identifier.new(),
        metadata_type=MetadataType.CATALOG,
        name="Assortment",
        source_definition_id=Identifier.new(),
    )

    with pytest.raises(AttributeError):
        metadata.name = "Other"  # type: ignore[misc]


def test_normalized_content_is_immutable() -> None:
    metadata = Metadata(
        identifier=Identifier.new(),
        metadata_type=MetadataType.CATALOG,
        name="Assortment",
        source_definition_id=Identifier.new(),
        normalized_content=(("kind", "catalog"),),
    )

    assert metadata.normalized_content == (("kind", "catalog"),)
