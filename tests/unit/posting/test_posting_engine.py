from datetime import UTC, datetime

from accore.platform.configuration import (
    ActiveConfiguration,
    ConfigurationIdentity,
    ConfigurationVersion,
    RuntimeConfigurationContext,
)
from accore.platform.foundation import Identifier
from accore.platform.object import ObjectContext, ObjectInstance
from accore.platform.persistence.errors import PersistenceFailure, PersistenceIndeterminateError
from accore.platform.posting import (
    DefaultPostingAPI,
    MappingPostingHandlerResolver,
    PostingContextFactory,
    PostingEngine,
    PostingOutcome,
    PostingServices,
)
from accore.platform.registers import DefaultMovementValidator
from accore.platform.runtime import (
    BusinessStateSnapshot,
    DurableFieldState,
    DurableReferenceState,
    DurableSystemFieldState,
    RuntimeDurableState,
)
from standard.posting import (
    INVENTORY_REGISTER_ID,
    GoodsReceiptPostingHandler,
    InventoryRegisterPostingContract,
)


class FakeObjectType:
    def __init__(self, identity):
        self._identity = identity

    def metadata_identity(self):
        return self._identity


def make_document() -> ObjectInstance:
    configuration = ActiveConfiguration(
        identity=ConfigurationIdentity("test"),
        version=ConfigurationVersion(1),
        published_metadata=__import__(
            "accore.platform.metadata", fromlist=["PublishedMetadataView"]
        ).PublishedMetadataView(()),
    )
    context = ObjectContext(RuntimeConfigurationContext(configuration))
    return ObjectInstance(Identifier.new(), FakeObjectType(Identifier.new()), context)


def line(product: str, warehouse: str, quantity: str):
    from decimal import Decimal

    from accore.platform.value import StructuredValue

    return StructuredValue(
        {
            "product": product,
            "warehouse": warehouse,
            "quantity": Decimal(quantity),
        }
    )


def state(*lines):
    from accore.platform.value import CollectionValue

    return RuntimeDurableState(
        fields=DurableFieldState({"lines": CollectionValue(lines)}),
        references=DurableReferenceState.empty(),
        business_state=BusinessStateSnapshot.empty(),
        system_fields=DurableSystemFieldState.empty(),
    )


class FixedClock:
    def __init__(self, value):
        self.value = value

    def now(self):
        return self.value


class StateProvider:
    def __init__(self, states):
        self.states = states

    def get(self, document):
        return self.states[document.identity]


class ContractResolver:
    def resolve(self, identity):
        if identity != INVENTORY_REGISTER_ID:
            raise KeyError(identity)
        return InventoryRegisterPostingContract()


class Coordinator:
    def __init__(self):
        self.effects = {}
        self.fail_with = None

    def establish(self, document, movement_set):
        if self.fail_with is not None:
            error, self.fail_with = self.fail_with, None
            raise error
        self.effects[document.identity] = tuple(movement_set.movements)

    def remove(self, document):
        if self.fail_with is not None:
            error, self.fail_with = self.fail_with, None
            raise error
        self.effects.pop(document.identity, None)

    def movements_for(self, document):
        return self.effects.get(document.identity, ())

    def inventory_quantity(self, product, warehouse):
        total = 0
        for movements in self.effects.values():
            for movement in movements:
                if (
                    movement.dimensions.get("product") == product
                    and movement.dimensions.get("warehouse") == warehouse
                ):
                    total += movement.resources.get("quantity", 0)
        return total


def build_api(document, document_state, clock, coordinator=None):
    coordinator = coordinator or Coordinator()
    resolver = MappingPostingHandlerResolver(
        {document.object_type.metadata_identity(): GoodsReceiptPostingHandler()}
    )
    validator = DefaultMovementValidator(ContractResolver())
    services = PostingServices(StateProvider({document.identity: document_state}))
    engine = PostingEngine(resolver, PostingContextFactory(services, clock), validator, coordinator)
    return DefaultPostingAPI(engine), coordinator


def test_posting_generates_inventory_fact() -> None:
    document = make_document()
    clock = FixedClock(datetime(2026, 9, 16, 12, 0, tzinfo=UTC))
    api, coordinator = build_api(document, state(line("P1", "W1", "2.5")), clock)

    result = api.post(document)

    assert result.outcome is PostingOutcome.SUCCESS
    movements = coordinator.movements_for(document)
    assert len(movements) == 1
    assert movements[0].source_document_identity == document.identity
    assert movements[0].dimensions.get("product") == "P1"
    assert movements[0].dimensions.get("warehouse") == "W1"
    assert movements[0].resources.get("quantity") == __import__("decimal").Decimal("2.5")
    assert movements[0].accounting_time == clock.now()
    assert coordinator.inventory_quantity("P1", "W1") == __import__("decimal").Decimal("2.5")


def test_empty_goods_receipt_fails_without_effect() -> None:
    document = make_document()
    api, coordinator = build_api(
        document,
        state(),
        FixedClock(datetime(2026, 9, 16, 12, 0, tzinfo=UTC)),
    )

    result = api.post(document)

    assert result.is_failure
    assert coordinator.movements_for(document) == ()


def test_repost_replaces_old_inventory_effects() -> None:
    document = make_document()
    clock = FixedClock(datetime(2026, 9, 16, 12, 0, tzinfo=UTC))
    api, coordinator = build_api(document, state(line("P1", "W1", "2")), clock)

    assert api.post(document).is_success
    assert coordinator.inventory_quantity("P1", "W1") == 2

    # The provider is deliberately replaced to model the current document state.
    api, _ = build_api(document, state(line("P1", "W1", "5")), clock, coordinator)
    assert api.repost(document).is_success
    assert coordinator.inventory_quantity("P1", "W1") == 5


def test_unpost_removes_inventory_effect() -> None:
    document = make_document()
    api, coordinator = build_api(
        document, state(line("P1", "W1", "3")), FixedClock(datetime(2026, 9, 16, tzinfo=UTC))
    )
    assert api.post(document).is_success
    assert api.unpost(document).is_success
    assert coordinator.inventory_quantity("P1", "W1") == 0


def test_known_persistence_failure_is_failure() -> None:
    document = make_document()
    clock = FixedClock(datetime(2026, 9, 16, tzinfo=UTC))
    api, coordinator = build_api(document, state(line("P1", "W1", "1")), clock)
    coordinator.fail_with = PersistenceFailure("write failed")

    result = api.post(document)

    assert result.is_failure


def test_indeterminate_persistence_failure_is_indeterminate() -> None:
    document = make_document()
    clock = FixedClock(datetime(2026, 9, 16, tzinfo=UTC))
    api, coordinator = build_api(document, state(line("P1", "W1", "1")), clock)
    coordinator.fail_with = PersistenceIndeterminateError("unknown")

    result = api.post(document)

    assert result.is_indeterminate
