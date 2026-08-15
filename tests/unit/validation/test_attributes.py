from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from accore.platform.definitions.attribute import AttributeDefinition, AttributeType
from accore.platform.foundation import DefinitionError
from accore.platform.validation.attributes import validate_attribute


def test_string_default_is_valid() -> None:
    attribute = AttributeDefinition(
        name="name",
        attribute_type=AttributeType.STRING,
        default_value="Product",
    )

    validate_attribute(attribute)


def test_integer_default_is_valid() -> None:
    attribute = AttributeDefinition(
        name="quantity",
        attribute_type=AttributeType.INTEGER,
        default_value=10,
    )

    validate_attribute(attribute)


def test_decimal_default_is_valid() -> None:
    attribute = AttributeDefinition(
        name="price",
        attribute_type=AttributeType.DECIMAL,
        default_value=Decimal("10.50"),
    )

    validate_attribute(attribute)


def test_boolean_default_is_valid() -> None:
    attribute = AttributeDefinition(
        name="active",
        attribute_type=AttributeType.BOOLEAN,
        default_value=True,
    )

    validate_attribute(attribute)


def test_date_default_is_valid() -> None:
    attribute = AttributeDefinition(
        name="start_date",
        attribute_type=AttributeType.DATE,
        default_value=date(2026, 1, 1),
    )

    validate_attribute(attribute)


def test_datetime_default_is_valid() -> None:
    attribute = AttributeDefinition(
        name="created_at",
        attribute_type=AttributeType.DATETIME,
        default_value=datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
    )

    validate_attribute(attribute)


def test_reference_default_is_valid() -> None:
    attribute = AttributeDefinition(
        name="unit",
        attribute_type=AttributeType.REFERENCE,
        reference_target="MeasureUnits",
        default_value="piece",
    )

    validate_attribute(attribute)


def test_enum_default_is_valid() -> None:
    attribute = AttributeDefinition(
        name="status",
        attribute_type=AttributeType.ENUM,
        default_value="active",
    )

    validate_attribute(attribute)


def test_integer_rejects_string_default() -> None:
    attribute = AttributeDefinition(
        name="quantity",
        attribute_type=AttributeType.INTEGER,
        default_value="10",
    )

    with pytest.raises(DefinitionError):
        validate_attribute(attribute)


def test_boolean_rejects_integer_default() -> None:
    attribute = AttributeDefinition(
        name="active",
        attribute_type=AttributeType.BOOLEAN,
        default_value=1,
    )

    with pytest.raises(DefinitionError):
        validate_attribute(attribute)


def test_integer_rejects_boolean_default() -> None:
    attribute = AttributeDefinition(
        name="quantity",
        attribute_type=AttributeType.INTEGER,
        default_value=True,
    )

    with pytest.raises(DefinitionError):
        validate_attribute(attribute)


def test_date_rejects_datetime_default() -> None:
    attribute = AttributeDefinition(
        name="start_date",
        attribute_type=AttributeType.DATE,
        default_value=datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
    )

    with pytest.raises(DefinitionError):
        validate_attribute(attribute)
