from accore.platform.definitions import CatalogDefinition
from accore.platform.foundation import Identifier

ASSORTMENT_ID = Identifier.from_str("01ARZ3NDEKTSV4RRFFQ69G5FAV")


class AssortmentDefinition(CatalogDefinition):
    """Standard Assortment catalog definition."""

    def __init__(self) -> None:
        super().__init__(
            identifier=ASSORTMENT_ID,
            name="Assortment",
        )
