from unittest.mock import Mock

import pytest

from accore.platform.definitions import CatalogDefinition
from accore.platform.definitions.attribute import AttributeDefinition, AttributeType
from accore.platform.foundation import DefinitionError, Identifier
from accore.platform.metadata import MetadataCompiler
from accore.platform.metadata.catalog import CatalogMetadata
from accore.platform.metadata.system_field import SystemFieldType


def test_catalog_definition_compiles_to_catalog_metadata() -> None:
    definition_id = Identifier.new()

    definition = CatalogDefinition(
        identifier=definition_id,
        name="Assortment",
    )

    compiler = MetadataCompiler()

    metadata = compiler.compile(definition)

    assert isinstance(metadata, CatalogMetadata)
    assert metadata.identifier == definition_id
    assert metadata.source_definition_id == definition_id
    assert metadata.name == "Assortment"


def test_invalid_definition_fails_compilation() -> None:
    definition = CatalogDefinition(
        identifier=Identifier.new(),
        name="",
    )

    compiler = MetadataCompiler()

    with pytest.raises(DefinitionError):
        compiler.compile(definition)


def test_compilation_is_deterministic() -> None:
    definition_id = Identifier.new()

    definition = CatalogDefinition(
        identifier=definition_id,
        name="Assortment",
        attributes=(
            AttributeDefinition(
                name="code",
                attribute_type=AttributeType.STRING,
                nullable=False,
                default_value="",
            ),
            AttributeDefinition(
                name="unit",
                attribute_type=AttributeType.REFERENCE,
                reference_target="MeasureUnits",
            ),
        ),
    )

    compiler = MetadataCompiler()

    first = compiler.compile(definition)
    second = compiler.compile(definition)

    assert first == second


def test_compiler_rejects_unsupported_definition() -> None:
    class UnsupportedDefinition:
        pass

    compiler = MetadataCompiler()

    with pytest.raises(TypeError):
        compiler.compile(UnsupportedDefinition())  # type: ignore[arg-type]


def test_catalog_definition_attributes_compile_to_metadata() -> None:
    definition_id = Identifier.new()

    definition = CatalogDefinition(
        identifier=definition_id,
        name="Assortment",
        attributes=(
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
            AttributeDefinition(
                name="unit",
                attribute_type=AttributeType.REFERENCE,
                reference_target="MeasureUnits",
            ),
        ),
    )

    compiler = MetadataCompiler()

    metadata = compiler.compile(definition)

    assert len(metadata.attributes) == 3

    assert metadata.attributes[0].name == "code"
    assert metadata.attributes[0].attribute_type is AttributeType.STRING
    assert metadata.attributes[0].nullable is False

    assert metadata.attributes[1].name == "name"
    assert metadata.attributes[1].attribute_type is AttributeType.STRING

    assert metadata.attributes[2].name == "unit"
    assert metadata.attributes[2].attribute_type is AttributeType.REFERENCE
    assert metadata.attributes[2].reference_target == "MeasureUnits"


def test_invalid_attribute_fails_compilation() -> None:
    definition = CatalogDefinition(
        identifier=Identifier.new(),
        name="Assortment",
        attributes=(
            AttributeDefinition(
                name="unit",
                attribute_type=AttributeType.REFERENCE,
            ),
        ),
    )

    compiler = MetadataCompiler()

    with pytest.raises(DefinitionError):
        compiler.compile(definition)


def test_attribute_compilation_is_deterministic() -> None:
    definition_id = Identifier.new()

    definition = CatalogDefinition(
        identifier=definition_id,
        name="Assortment",
        attributes=(
            AttributeDefinition(
                name="code",
                attribute_type=AttributeType.STRING,
                nullable=False,
            ),
            AttributeDefinition(
                name="unit",
                attribute_type=AttributeType.REFERENCE,
                reference_target="MeasureUnits",
            ),
        ),
    )

    compiler = MetadataCompiler()

    first = compiler.compile(definition)
    second = compiler.compile(definition)

    assert first == second


def test_catalog_compilation_adds_system_fields() -> None:
    definition = CatalogDefinition(
        identifier=Identifier.new(),
        name="Assortment",
    )

    metadata = MetadataCompiler().compile(definition)

    assert [field.name for field in metadata.system_fields] == [
        "id",
        "parent_id",
        "is_folder",
        "created_at",
        "updated_at",
        "deleted",
        "version",
    ]

    assert metadata.system_fields[0].field_type is SystemFieldType.ULID


def test_system_fields_are_independent_from_definition_attributes() -> None:
    definition = CatalogDefinition(
        identifier=Identifier.new(),
        name="Assortment",
        attributes=(
            AttributeDefinition(
                name="name",
                attribute_type=AttributeType.STRING,
            ),
        ),
    )

    metadata = MetadataCompiler().compile(definition)

    system_names = {field.name for field in metadata.system_fields}

    attribute_names = {attribute.name for attribute in metadata.attributes}

    assert "id" in system_names
    assert "id" not in attribute_names
    assert "name" in attribute_names


def test_compiler_delegates_validation_once() -> None:
    definition = CatalogDefinition(
        identifier=Identifier.new(),
        name="Assortment",
        attributes=(),
    )

    validator = Mock()
    compiler = MetadataCompiler(validator=validator)

    compiler.compile(definition)

    validator.validate.assert_called_once_with(definition)


def test_compiler_preserves_identity() -> None:
    definition_id = Identifier.new()

    definition = CatalogDefinition(
        identifier=definition_id,
        name="Assortment",
    )

    metadata = MetadataCompiler().compile(definition)

    assert metadata.identifier == definition_id
    assert metadata.source_definition_id == definition_id


def test_compiler_preserves_name() -> None:
    definition = CatalogDefinition(
        identifier=Identifier.new(),
        name="Assortment",
    )

    metadata = MetadataCompiler().compile(definition)

    assert metadata.name == "Assortment"


def test_compiler_preserves_attribute_properties() -> None:
    definition = CatalogDefinition(
        identifier=Identifier.new(),
        name="Assortment",
        attributes=(
            AttributeDefinition(
                name="code",
                attribute_type=AttributeType.STRING,
                nullable=False,
                default_value="",
                description="Item code",
            ),
            AttributeDefinition(
                name="unit",
                attribute_type=AttributeType.REFERENCE,
                reference_target="MeasureUnits",
            ),
        ),
    )
    metadata = MetadataCompiler().compile(definition)

    code = metadata.attributes[0]
    unit = metadata.attributes[1]

    assert code.name == "code"
    assert code.attribute_type is AttributeType.STRING
    assert code.nullable is False
    assert code.default_value == ""
    assert code.description == "Item code"
    assert code.reference_target is None

    assert unit.name == "unit"
    assert unit.attribute_type is AttributeType.REFERENCE
    assert unit.nullable is True
    assert unit.reference_target == "MeasureUnits"


def test_compiler_preserves_attribute_order() -> None:
    definition = CatalogDefinition(
        identifier=Identifier.new(),
        name="Assortment",
        attributes=(
            AttributeDefinition(
                name="name",
                attribute_type=AttributeType.STRING,
            ),
            AttributeDefinition(
                name="code",
                attribute_type=AttributeType.STRING,
            ),
            AttributeDefinition(
                name="unit",
                attribute_type=AttributeType.REFERENCE,
                reference_target="MeasureUnits",
            ),
        ),
    )

    metadata = MetadataCompiler().compile(definition)

    assert [attribute.name for attribute in metadata.attributes] == [
        "name",
        "code",
        "unit",
    ]


def test_compiler_does_not_introduce_normalized_content() -> None:
    definition = CatalogDefinition(
        identifier=Identifier.new(),
        name="Assortment",
    )

    metadata = MetadataCompiler().compile(definition)

    assert metadata.normalized_content == ()
