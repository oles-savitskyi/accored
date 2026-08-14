import pytest

from accore.platform.definitions.attribute import AttributeDefinition, AttributeType
from accore.platform.definitions.base import DefinitionType
from accore.platform.definitions.catalog import CatalogDefinition
from accore.platform.foundation import DefinitionError, Identifier


def test_valid_catalog_definition() -> None:
    catalog = CatalogDefinition(
        identifier=Identifier.new(),
        name="Assortment",
    )

    catalog.validate()

    assert catalog.definition_type is DefinitionType.CATALOG
    assert catalog.name == "Assortment"


def test_catalog_definition_requires_identifier() -> None:
    catalog = CatalogDefinition(
        identifier=None,
        name="Assortment",
    )

    with pytest.raises(DefinitionError):
        catalog.validate()


def test_catalog_definition_requires_name() -> None:
    catalog = CatalogDefinition(
        identifier=Identifier.new(),
        name="",
    )

    with pytest.raises(DefinitionError):
        catalog.validate()


def test_catalog_definition_is_a_definition() -> None:
    catalog = CatalogDefinition(
        identifier=Identifier.new(),
        name="Assortment",
    )

    assert isinstance(catalog, CatalogDefinition)


def test_catalog_definition_contains_attributes() -> None:
    attributes = (
        AttributeDefinition(
            name="code",
            attribute_type=AttributeType.STRING,
            nullable=False,
        ),
        AttributeDefinition(
            name="name",
            attribute_type=AttributeType.STRING,
            nullable=False,
        ),
    )

    catalog = CatalogDefinition(
        identifier=Identifier.new(),
        name="Assortment",
        attributes=attributes,
    )

    catalog.validate()

    assert catalog.attributes == attributes


def test_catalog_definition_rejects_duplicate_attribute_names() -> None:
    attributes = (
        AttributeDefinition(
            name="code",
            attribute_type=AttributeType.STRING,
        ),
        AttributeDefinition(
            name="code",
            attribute_type=AttributeType.STRING,
        ),
    )

    catalog = CatalogDefinition(
        identifier=Identifier.new(),
        name="Assortment",
        attributes=attributes,
    )

    with pytest.raises(DefinitionError):
        catalog.validate()
