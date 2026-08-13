import pytest

from accore.platform.definitions.base import Definition, DefinitionType
from accore.platform.foundation import DefinitionError, Identifier


def test_valid_definition() -> None:
    definition = Definition(
        identifier=Identifier.new(),
        name="Assortment",
        definition_type=DefinitionType.CATALOG,
    )

    definition.validate()


def test_missing_identifier() -> None:
    definition = Definition(
        identifier=None,
        name="Assortment",
        definition_type=DefinitionType.CATALOG,
    )

    with pytest.raises(DefinitionError):
        definition.validate()


def test_invalid_identifier() -> None:
    with pytest.raises(ValueError):
        Identifier.from_str("not-a-valid-ulid")


def test_missing_name() -> None:
    definition = Definition(
        identifier=Identifier.new(),
        name="",
        definition_type=DefinitionType.CATALOG,
    )

    with pytest.raises(DefinitionError):
        definition.validate()


def test_whitespace_only_name() -> None:
    definition = Definition(
        identifier=Identifier.new(),
        name="   ",
        definition_type=DefinitionType.CATALOG,
    )

    with pytest.raises(DefinitionError):
        definition.validate()


def test_definition_is_immutable() -> None:
    definition = Definition(
        identifier=Identifier.new(),
        name="Assortment",
        definition_type=DefinitionType.CATALOG,
    )

    with pytest.raises(AttributeError):
        definition.name = "Other"  # type: ignore[misc]
