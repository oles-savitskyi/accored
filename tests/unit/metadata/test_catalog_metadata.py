import pytest

from accore.platform.definitions.attribute import AttributeType
from accore.platform.foundation import Identifier
from accore.platform.metadata.attribute import AttributeMetadata
from accore.platform.metadata.base import MetadataType
from accore.platform.metadata.catalog import CatalogMetadata


def test_valid_catalog_metadata() -> None:
    metadata = CatalogMetadata(
        identifier=Identifier.new(),
        name="Assortment",
        source_definition_id=Identifier.new(),
    )

    assert metadata.metadata_type is MetadataType.CATALOG
    assert metadata.name == "Assortment"


def test_catalog_metadata_preserves_identity() -> None:
    metadata_id = Identifier.new()
    definition_id = Identifier.new()

    metadata = CatalogMetadata(
        identifier=metadata_id,
        name="Assortment",
        source_definition_id=definition_id,
    )

    assert metadata.identifier == metadata_id
    assert metadata.source_definition_id == definition_id


def test_catalog_metadata_is_immutable() -> None:
    metadata = CatalogMetadata(
        identifier=Identifier.new(),
        name="Assortment",
        source_definition_id=Identifier.new(),
    )

    with pytest.raises(AttributeError):
        metadata.name = "Other"  # type: ignore[misc]


def test_catalog_metadata_preserves_normalized_content() -> None:
    content = (("kind", "catalog"),)

    metadata = CatalogMetadata(
        identifier=Identifier.new(),
        name="Assortment",
        source_definition_id=Identifier.new(),
        normalized_content=content,
    )

    assert metadata.normalized_content == content


def test_catalog_metadata_contains_attributes() -> None:
    attributes = (
        AttributeMetadata(
            name="code",
            attribute_type=AttributeType.STRING,
            nullable=False,
        ),
        AttributeMetadata(
            name="name",
            attribute_type=AttributeType.STRING,
            nullable=False,
        ),
    )

    metadata = CatalogMetadata(
        identifier=Identifier.new(),
        name="Assortment",
        source_definition_id=Identifier.new(),
        attributes=attributes,
    )

    assert metadata.attributes == attributes
    assert metadata.attributes[0].name == "code"
    assert metadata.attributes[1].name == "name"


def test_catalog_metadata_attributes_are_immutable() -> None:
    metadata = CatalogMetadata(
        identifier=Identifier.new(),
        name="Assortment",
        source_definition_id=Identifier.new(),
        attributes=(
            AttributeMetadata(
                name="code",
                attribute_type=AttributeType.STRING,
            ),
        ),
    )

    with pytest.raises(AttributeError):
        metadata.attributes = ()  # type: ignore[misc]
