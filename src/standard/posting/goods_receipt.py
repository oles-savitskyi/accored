from __future__ import annotations

from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.posting import PostingContext, PostingValidationError
from accore.platform.posting.movement_set import MovementSet
from accore.platform.registers import (
    Movement,
    MovementAttributes,
    MovementDimensions,
    MovementResources,
    MovementType,
)
from accore.platform.value import CollectionValue, StructuredValue

INVENTORY_REGISTER_ID = Identifier.from_str("01ARZ3NDEKTSV4RRFFQ69G5FAT")
GOODS_RECEIPT_MOVEMENT_TYPE = MovementType.INCOME
LINES_FIELD = "lines"
PRODUCT_FIELD = "product"
WAREHOUSE_FIELD = "warehouse"
QUANTITY_FIELD = "quantity"


class GoodsReceiptPostingHandler:
    def post(self, context: PostingContext) -> MovementSet:
        state = context.services.document_state.get(context.document)
        raw_lines = state.fields.get(LINES_FIELD)

        if not isinstance(raw_lines, CollectionValue):
            raise PostingValidationError("Goods Receipt must contain a lines collection.")
        if len(raw_lines) == 0:
            raise PostingValidationError("Empty Goods Receipt cannot be posted.")

        movements: list[Movement] = []
        for index, raw_line in enumerate(raw_lines):
            if not isinstance(raw_line, StructuredValue):
                raise PostingValidationError(f"Goods Receipt line {index} is invalid.")

            product = raw_line.get(PRODUCT_FIELD)
            warehouse = raw_line.get(WAREHOUSE_FIELD)
            quantity = raw_line.get(QUANTITY_FIELD)

            if not isinstance(product, str) or not product.strip():
                raise PostingValidationError(f"Goods Receipt line {index} requires Product.")
            if not isinstance(warehouse, str) or not warehouse.strip():
                raise PostingValidationError(f"Goods Receipt line {index} requires Warehouse.")
            if not isinstance(quantity, Decimal) or quantity <= 0:
                raise PostingValidationError(
                    f"Goods Receipt line {index} requires a positive Decimal Quantity."
                )

            movements.append(
                Movement(
                    identity=_movement_identity(context.document.identity, index),
                    source_document_identity=context.document.identity,
                    register_identity=INVENTORY_REGISTER_ID,
                    movement_type=GOODS_RECEIPT_MOVEMENT_TYPE,
                    dimensions=MovementDimensions.from_mapping(
                        {PRODUCT_FIELD: product, WAREHOUSE_FIELD: warehouse}
                    ),
                    resources=MovementResources.from_mapping({QUANTITY_FIELD: quantity}),
                    attributes=MovementAttributes.from_mapping({}),
                    accounting_time=context.clock.now(),
                )
            )

        return MovementSet(tuple(movements))


def _movement_identity(source: Identifier, line_index: int) -> Identifier:
    """Derive a deterministic distinct identity for a source document line."""
    if line_index < 0 or line_index >= 1024:
        raise ValueError("Goods Receipt line index is outside the supported range.")
    alphabet = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    suffix = alphabet[(line_index // 32) % 32] + alphabet[line_index % 32]
    source_text = str(source)
    return Identifier.from_str(source_text[:-2] + suffix)
