from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from accore.platform.definitions.attribute import AttributeDefinition, AttributeType
from accore.platform.foundation import DefinitionError


def validate_attribute(attribute: AttributeDefinition) -> None:
    """Validate an attribute definition completely."""

    attribute.validate()
    validate_attribute_semantics(attribute)


def validate_attribute_semantics(attribute: AttributeDefinition) -> None:
    """Validate semantic constraints of an already structurally valid attribute."""

    if attribute.default_value is None:
        return

    expected_type = _expected_type(attribute.attribute_type)

    if expected_type is None:
        return

    if not _matches_type(attribute.default_value, expected_type):
        raise DefinitionError(
            f"Default value for attribute '{attribute.name}' "
            f"must be of type {expected_type.__name__}."
        )


def _expected_type(attribute_type: AttributeType) -> type[Any] | None:
    return {
        AttributeType.STRING: str,
        AttributeType.INTEGER: int,
        AttributeType.DECIMAL: Decimal,
        AttributeType.BOOLEAN: bool,
        AttributeType.DATE: date,
        AttributeType.DATETIME: datetime,
        AttributeType.REFERENCE: str,
        AttributeType.ENUM: str,
    }.get(attribute_type)


def _matches_type(value: Any, expected_type: type[Any]) -> bool:
    if expected_type in (bool, int, date):
        return type(value) is expected_type

    return isinstance(value, expected_type)
