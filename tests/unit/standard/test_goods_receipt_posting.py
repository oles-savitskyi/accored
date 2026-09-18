from datetime import UTC, datetime
from decimal import Decimal

from accore.platform.configuration import (
    ActiveConfiguration,
    ConfigurationIdentity,
    ConfigurationVersion,
    RuntimeConfigurationContext,
)
from accore.platform.foundation import Identifier
from accore.platform.object import ObjectContext, ObjectInstance
from accore.platform.posting import PostingContext, PostingServices
from accore.platform.runtime import (
    BusinessStateSnapshot,
    DurableFieldState,
    DurableReferenceState,
    DurableSystemFieldState,
    RuntimeDurableState,
)
from accore.platform.value import CollectionValue, StructuredValue
from standard.posting import (
    GOODS_RECEIPT_MOVEMENT_TYPE,
    INVENTORY_REGISTER_ID,
    GoodsReceiptPostingHandler,
)


class Clock:
    def now(self):
        return datetime(2026, 9, 16, 10, 0, tzinfo=UTC)


class States:
    def __init__(self, state):
        self.state = state

    def get(self, document):
        return self.state


def test_goods_receipt_handler_maps_lines_deterministically() -> None:
    identity = Identifier.new()

    class FakeObjectType:
        def metadata_identity(self):
            return identity

    config = ActiveConfiguration(
        ConfigurationIdentity("test"),
        ConfigurationVersion(1),
        __import__(
            "accore.platform.metadata", fromlist=["PublishedMetadataView"]
        ).PublishedMetadataView(()),
    )
    document = ObjectInstance(
        Identifier.new(), FakeObjectType(), ObjectContext(RuntimeConfigurationContext(config))
    )
    state = RuntimeDurableState(
        DurableFieldState(
            {
                "lines": CollectionValue(
                    (
                        StructuredValue(
                            {"product": "P1", "warehouse": "W1", "quantity": Decimal(2)}
                        ),
                        StructuredValue(
                            {"product": "P2", "warehouse": "W2", "quantity": Decimal(3)}
                        ),
                    )
                )
            }
        ),
        DurableReferenceState.empty(),
        BusinessStateSnapshot.empty(),
        DurableSystemFieldState.empty(),
    )
    context = PostingContext(
        document, config.published_metadata, PostingServices(States(state)), Clock()
    )

    result = GoodsReceiptPostingHandler().post(context)

    assert [m.dimensions.get("product") for m in result.movements] == ["P1", "P2"]
    assert all(m.register_identity == INVENTORY_REGISTER_ID for m in result.movements)
    assert all(m.movement_type is GOODS_RECEIPT_MOVEMENT_TYPE for m in result.movements)
