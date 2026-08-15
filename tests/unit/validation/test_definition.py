import pytest

from accore.platform.definitions import CatalogDefinition
from accore.platform.definitions.attribute import AttributeDefinition, AttributeType
from accore.platform.foundation import DefinitionError, Identifier
from accore.platform.validation import DefinitionValidator


def test_validator_accepts_valid_catalog() -> None:
    definition = CatalogDefinition(
        identifier=Identifier.new(),
        name="Assortment",
        attributes=(
            AttributeDefinition(
                name="name",
                attribute_type=AttributeType.STRING,
            ),
            AttributeDefinition(
                name="quantity",
                attribute_type=AttributeType.INTEGER,
                default_value=0,
            ),
        ),
    )

    DefinitionValidator().validate(definition)


def test_validator_rejects_invalid_catalog_attribute() -> None:
    definition = CatalogDefinition(
        identifier=Identifier.new(),
        name="Assortment",
        attributes=(
            AttributeDefinition(
                name="quantity",
                attribute_type=AttributeType.INTEGER,
                default_value="invalid",
            ),
        ),
    )

    with pytest.raises(DefinitionError):
        DefinitionValidator().validate(definition)


def test_validator_rejects_duplicate_attribute_names() -> None:
    definition = CatalogDefinition(
        identifier=Identifier.new(),
        name="Assortment",
        attributes=(
            AttributeDefinition(
                name="name",
                attribute_type=AttributeType.STRING,
            ),
            AttributeDefinition(
                name="name",
                attribute_type=AttributeType.STRING,
            ),
        ),
    )

    with pytest.raises(DefinitionError):
        DefinitionValidator().validate(definition)


def test_validator_does_not_resolve_reference_target() -> None:
    definition = CatalogDefinition(
        identifier=Identifier.new(),
        name="Assortment",
        attributes=(
            AttributeDefinition(
                name="unit",
                attribute_type=AttributeType.REFERENCE,
                reference_target="UnknownCatalog",
            ),
        ),
    )

    DefinitionValidator().validate(definition)


def test_validator_rejects_unsupported_definition() -> None:
    class UnsupportedDefinition:
        pass

    with pytest.raises(TypeError):
        DefinitionValidator().validate(UnsupportedDefinition())  # type: ignore[arg-type]
