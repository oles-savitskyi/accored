from __future__ import annotations

from accore.platform.definitions import CatalogDefinition
from accore.platform.foundation import Identifier

ASSORTMENT_ID = Identifier.from_str("01ARZ3NDEKTSV4RRFFQ69G5FAV")


def standard_catalog_definitions() -> tuple[CatalogDefinition, ...]:
    """Return the standard catalog definitions."""
    return (
        CatalogDefinition(
            identifier=ASSORTMENT_ID,
            name="Assortment",
        ),
    )
