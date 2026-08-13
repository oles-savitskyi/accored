from accore.platform.definitions import CatalogDefinition
from standard.definitions.catalogs import standard_catalog_definitions


def test_standard_catalog_definition_identity_is_deterministic() -> None:
    first = standard_catalog_definitions()
    second = standard_catalog_definitions()

    assert first[0].identifier == second[0].identifier
    assert first[0].name == "Assortment"


def test_standard_catalog_definitions_contains_assortment() -> None:
    definitions = standard_catalog_definitions()

    assert len(definitions) == 1

    assortment = definitions[0]

    assert isinstance(assortment, CatalogDefinition)
    assert assortment.name == "Assortment"
    assert assortment.identifier is not None
