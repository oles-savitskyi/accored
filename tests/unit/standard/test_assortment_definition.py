from standard.definitions.assortment import (
    ASSORTMENT_ID,
    AssortmentDefinition,
)


def test_assortment_definition_is_valid() -> None:
    definition = AssortmentDefinition()

    definition.validate()

    assert definition.identifier == ASSORTMENT_ID
    assert definition.name == "Assortment"


from accore.platform.metadata import MetadataCompiler


def test_assortment_definition_compiles() -> None:
    definition = AssortmentDefinition()

    metadata = MetadataCompiler().compile(definition)

    assert metadata.name == "Assortment"
