import pytest

from accore.platform.definitions.attribute import AttributeDefinition, AttributeType
from accore.platform.foundation import DefinitionError


def test_valid_string_attribute_definition() -> None:
    attribute = AttributeDefinition(
        name="code",
        attribute_type=AttributeType.STRING,
        nullable=False,
    )

    attribute.validate()

    assert attribute.name == "code"
    assert attribute.attribute_type is AttributeType.STRING
    assert attribute.nullable is False


def test_attribute_definition_requires_name() -> None:
    attribute = AttributeDefinition(
        name="",
        attribute_type=AttributeType.STRING,
    )

    with pytest.raises(DefinitionError):
        attribute.validate()


@pytest.mark.parametrize(
    "attribute_type",
    [
        AttributeType.STRING,
        AttributeType.INTEGER,
        AttributeType.DECIMAL,
        AttributeType.BOOLEAN,
        AttributeType.DATE,
        AttributeType.DATETIME,
        AttributeType.REFERENCE,
        AttributeType.ENUM,
    ],
)
def test_supported_attribute_types_are_available(
    attribute_type: AttributeType,
) -> None:
    if attribute_type is AttributeType.REFERENCE:
        attribute = AttributeDefinition(
            name="unit",
            attribute_type=attribute_type,
            reference_target="MeasureUnits",
        )
    else:
        attribute = AttributeDefinition(
            name="value",
            attribute_type=attribute_type,
        )

    attribute.validate()


def test_reference_attribute_requires_target() -> None:
    attribute = AttributeDefinition(
        name="unit",
        attribute_type=AttributeType.REFERENCE,
    )

    with pytest.raises(DefinitionError):
        attribute.validate()


def test_non_reference_attribute_rejects_reference_target() -> None:
    attribute = AttributeDefinition(
        name="code",
        attribute_type=AttributeType.STRING,
        reference_target="MeasureUnits",
    )

    with pytest.raises(DefinitionError):
        attribute.validate()


def test_attribute_definition_is_immutable() -> None:
    attribute = AttributeDefinition(
        name="code",
        attribute_type=AttributeType.STRING,
    )

    with pytest.raises(AttributeError):
        attribute.name = "other"  # type: ignore[misc]
