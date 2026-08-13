from accore.platform.definitions import CatalogDefinition
from standard.definitions.assortment import AssortmentDefinition


def standard_catalog_definitions() -> tuple[CatalogDefinition, ...]:
    return (AssortmentDefinition(),)
