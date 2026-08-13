import pytest

from accore.platform.definitions import CatalogDefinition
from accore.platform.foundation import DefinitionError, Identifier
from accore.platform.metadata import MetadataCompiler
from accore.platform.metadata.catalog import CatalogMetadata


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
