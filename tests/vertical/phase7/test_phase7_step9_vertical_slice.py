from datetime import UTC, datetime, timedelta
from decimal import Decimal

from accore.platform.configuration import (
    ActiveConfiguration,
    ConfigurationIdentity,
    ConfigurationVersion,
    RuntimeConfigurationContext,
)
from accore.platform.foundation import Identifier
from accore.platform.metadata.publication import PublishedMetadataView
from accore.platform.object import ObjectContext, ObjectInstance
from accore.platform.posting import (
    MappingPostingHandlerResolver,
    PostingContextFactory,
    PostingEngine,
    PostingOutcome,
    PostingServices,
)
from accore.platform.registers import (
    BalanceQuery,
    MovementDimensionFilter,
    MovementQuery,
    MovementQueryPeriod,
    MovementType,
    TotalsKey,
)
from accore.platform.runtime import (
    BusinessStateSnapshot,
    DurableFieldState,
    DurableReferenceState,
    DurableSystemFieldState,
    RuntimeDurableState,
)
from accore.platform.value import CollectionValue, StructuredValue
from standard.bootstrap import StandardConfigurationBootstrap
from standard.posting import GoodsReceiptPostingHandler
from standard.registers.inventory import (
    INVENTORY_PRODUCT_DIMENSION,
    INVENTORY_QUANTITY_RESOURCE,
    INVENTORY_REGISTER_ID,
    INVENTORY_WAREHOUSE_DIMENSION,
)


class FakeObjectType:
    def __init__(self, identity: Identifier) -> None:
        self._identity = identity

    def metadata_identity(self) -> Identifier:
        return self._identity


class InMemoryRegisterFactPersistence:
    def __init__(self) -> None:
        self.movements = {}

    def append(self, movements) -> None:
        for movement in movements:
            self.movements[movement.identity] = movement

    def find_by_source_document(
        self,
        register_identity: Identifier,
        source_document_identity: Identifier,
    ):
        return tuple(
            movement
            for movement in self.movements.values()
            if movement.register_identity == register_identity
            and movement.source_document_identity == source_document_identity
        )

    def remove(self, movement_identities) -> None:
        for identity in movement_identities:
            self.movements.pop(identity, None)

    def enumerate(self, register_identity: Identifier):
        return tuple(
            movement
            for movement in self.movements.values()
            if movement.register_identity == register_identity
        )


class FixedClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def now(self) -> datetime:
        return self.value


class StateProvider:
    def __init__(self, state: RuntimeDurableState) -> None:
        self.state = state

    def get(self, document: ObjectInstance) -> RuntimeDurableState:
        return self.state


def make_document() -> ObjectInstance:
    configuration = ActiveConfiguration(
        identity=ConfigurationIdentity("test"),
        version=ConfigurationVersion(1),
        published_metadata=PublishedMetadataView(()),
    )
    return ObjectInstance(
        Identifier.new(),
        FakeObjectType(Identifier.new()),
        ObjectContext(RuntimeConfigurationContext(configuration)),
    )


def make_state(*, product: str, warehouse: str, quantity: Decimal) -> RuntimeDurableState:
    return RuntimeDurableState(
        fields=DurableFieldState(
            {
                "lines": CollectionValue(
                    (
                        StructuredValue(
                            {
                                INVENTORY_PRODUCT_DIMENSION: product,
                                INVENTORY_WAREHOUSE_DIMENSION: warehouse,
                                INVENTORY_QUANTITY_RESOURCE: quantity,
                            }
                        ),
                    )
                )
            }
        ),
        references=DurableReferenceState.empty(),
        business_state=BusinessStateSnapshot.empty(),
        system_fields=DurableSystemFieldState.empty(),
    )


def make_engine(
    *,
    persistence: InMemoryRegisterFactPersistence,
    document: ObjectInstance,
    state_provider: StateProvider,
    accounting_time: datetime,
):
    composition = StandardConfigurationBootstrap().compose_inventory_register_platform(persistence)
    resolver = MappingPostingHandlerResolver(
        {document.object_type.metadata_identity(): GoodsReceiptPostingHandler()}
    )
    services = PostingServices(document_state=state_provider)
    engine = PostingEngine(
        handler_resolver=resolver,
        context_factory=PostingContextFactory(services, FixedClock(accounting_time)),
        movement_validator=composition.movement_validator,
        result_coordinator=composition.posting_result_coordinator,
    )
    return engine, composition


def post_goods_receipt(
    *,
    product: str,
    warehouse: str,
    quantity: str,
    accounting_time: datetime,
    persistence: InMemoryRegisterFactPersistence | None = None,
    composition=None,
):
    if persistence is None:
        persistence = InMemoryRegisterFactPersistence()
    if composition is None:
        composition = StandardConfigurationBootstrap().compose_inventory_register_platform(
            persistence
        )

    document = make_document()
    state_provider = StateProvider(
        make_state(
            product=product,
            warehouse=warehouse,
            quantity=Decimal(quantity),
        )
    )
    resolver = MappingPostingHandlerResolver(
        {document.object_type.metadata_identity(): GoodsReceiptPostingHandler()}
    )
    services = PostingServices(document_state=state_provider)
    engine = PostingEngine(
        handler_resolver=resolver,
        context_factory=PostingContextFactory(services, FixedClock(accounting_time)),
        movement_validator=composition.movement_validator,
        result_coordinator=composition.posting_result_coordinator,
    )
    result = engine.post(document)
    assert result.outcome is PostingOutcome.SUCCESS
    return persistence, document, state_provider, engine, composition


def inventory_key(*, product: str, warehouse: str) -> TotalsKey:
    return TotalsKey.from_mapping(
        {
            INVENTORY_PRODUCT_DIMENSION: product,
            INVENTORY_WAREHOUSE_DIMENSION: warehouse,
        }
    )


def assert_inventory_consistency(
    *,
    persistence: InMemoryRegisterFactPersistence,
    composition,
    product: str,
    warehouse: str,
) -> None:
    movements = tuple(persistence.enumerate(INVENTORY_REGISTER_ID))
    expected = Decimal(0)
    for movement in movements:
        if (
            movement.dimensions.get(INVENTORY_PRODUCT_DIMENSION) == product
            and movement.dimensions.get(INVENTORY_WAREHOUSE_DIMENSION) == warehouse
        ):
            quantity = movement.resources.get(INVENTORY_QUANTITY_RESOURCE)
            if movement.movement_type is MovementType.INCOME:
                expected += quantity
            elif movement.movement_type is MovementType.EXPENSE:
                expected -= quantity

    key = inventory_key(product=product, warehouse=warehouse)
    assert composition.totals_engine.get(INVENTORY_REGISTER_ID, key) == expected
    assert (
        composition.balance_query.query(
            BalanceQuery(
                register_identity=INVENTORY_REGISTER_ID,
                aggregation_scope=key,
            )
        ).value
        == expected
    )


def make_query(
    *,
    start: datetime,
    end: datetime,
    dimensions: dict[str, str] | None = None,
) -> MovementQuery:
    return MovementQuery(
        register_identity=INVENTORY_REGISTER_ID,
        period=MovementQueryPeriod(start=start, end=end),
        dimensions=MovementDimensionFilter.from_mapping(dimensions or {}),
    )


def test_goods_receipt_posting_persists_inventory_movement() -> None:
    accounting_time = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    persistence, document, _state_provider, _engine, _composition = post_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="2.5",
        accounting_time=accounting_time,
    )

    movements = tuple(persistence.enumerate(INVENTORY_REGISTER_ID))

    assert len(movements) == 1
    movement = movements[0]
    assert movement.register_identity == INVENTORY_REGISTER_ID
    assert movement.source_document_identity == document.identity
    assert movement.movement_type is MovementType.INCOME
    assert movement.dimensions.get(INVENTORY_PRODUCT_DIMENSION) == "P1"
    assert movement.dimensions.get(INVENTORY_WAREHOUSE_DIMENSION) == "W1"
    assert movement.resources.get(INVENTORY_QUANTITY_RESOURCE) == Decimal("2.5")
    assert movement.accounting_time == accounting_time


def test_posting_updates_inventory_totals_and_balance() -> None:
    persistence, _document, _state_provider, _engine, composition = post_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="2.5",
        accounting_time=datetime(2026, 9, 24, 12, 0, tzinfo=UTC),
    )
    key = inventory_key(product="P1", warehouse="W1")

    assert composition.totals_engine.get(INVENTORY_REGISTER_ID, key) == Decimal("2.5")
    assert composition.balance_query.query(
        BalanceQuery(
            register_identity=INVENTORY_REGISTER_ID,
            aggregation_scope=key,
        )
    ).value == Decimal("2.5")
    assert_inventory_consistency(
        persistence=persistence,
        composition=composition,
        product="P1",
        warehouse="W1",
    )


def test_unpost_removes_inventory_effect_from_persistence_totals_and_balance() -> None:
    persistence, document, _state_provider, engine, composition = post_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="2.5",
        accounting_time=datetime(2026, 9, 24, 12, 0, tzinfo=UTC),
    )
    key = inventory_key(product="P1", warehouse="W1")

    result = engine.unpost(document)

    assert result.is_success
    assert persistence.find_by_source_document(INVENTORY_REGISTER_ID, document.identity) == ()
    assert tuple(persistence.enumerate(INVENTORY_REGISTER_ID)) == ()
    assert composition.totals_engine.get(INVENTORY_REGISTER_ID, key) == Decimal(0)
    assert composition.balance_query.query(
        BalanceQuery(
            register_identity=INVENTORY_REGISTER_ID,
            aggregation_scope=key,
        )
    ).value == Decimal(0)


def test_repost_replaces_inventory_effect_with_new_quantity() -> None:
    persistence, document, state_provider, engine, composition = post_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="2.5",
        accounting_time=datetime(2026, 9, 24, 12, 0, tzinfo=UTC),
    )
    old_movements = persistence.find_by_source_document(INVENTORY_REGISTER_ID, document.identity)
    assert len(old_movements) == 1

    state_provider.state = make_state(
        product="P1",
        warehouse="W1",
        quantity=Decimal(15),
    )
    result = engine.repost(document)

    assert result.is_success
    movements = persistence.find_by_source_document(INVENTORY_REGISTER_ID, document.identity)
    assert len(movements) == 1
    assert movements[0].resources.get(INVENTORY_QUANTITY_RESOURCE) == Decimal(15)

    key = inventory_key(product="P1", warehouse="W1")
    assert composition.totals_engine.get(INVENTORY_REGISTER_ID, key) == Decimal(15)
    assert composition.balance_query.query(
        BalanceQuery(
            register_identity=INVENTORY_REGISTER_ID,
            aggregation_scope=key,
        )
    ).value == Decimal(15)


def test_inventory_movement_query_filters_by_product() -> None:
    start = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    persistence = InMemoryRegisterFactPersistence()
    composition = StandardConfigurationBootstrap().compose_inventory_register_platform(persistence)
    for product, warehouse, quantity, offset in (
        ("P1", "W1", "10", 0),
        ("P1", "W2", "20", 1),
        ("P2", "W1", "30", 2),
        ("P1", "W1", "5", 3),
    ):
        post_goods_receipt(
            product=product,
            warehouse=warehouse,
            quantity=quantity,
            accounting_time=start + timedelta(days=offset),
            persistence=persistence,
            composition=composition,
        )

    result = composition.movement_query.query(
        make_query(
            start=start - timedelta(hours=1),
            end=start + timedelta(days=4),
            dimensions={INVENTORY_PRODUCT_DIMENSION: "P1"},
        )
    )
    assert {movement.dimensions.get(INVENTORY_WAREHOUSE_DIMENSION) for movement in result} == {
        "W1",
        "W2",
    }
    assert len(result) == 3


def test_inventory_movement_query_filters_by_warehouse() -> None:
    start = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    persistence = InMemoryRegisterFactPersistence()
    composition = StandardConfigurationBootstrap().compose_inventory_register_platform(persistence)
    for product, warehouse, quantity, offset in (
        ("P1", "W1", "10", 0),
        ("P1", "W2", "20", 1),
        ("P2", "W1", "30", 2),
        ("P1", "W1", "5", 3),
    ):
        post_goods_receipt(
            product=product,
            warehouse=warehouse,
            quantity=quantity,
            accounting_time=start + timedelta(days=offset),
            persistence=persistence,
            composition=composition,
        )

    result = composition.movement_query.query(
        make_query(
            start=start - timedelta(hours=1),
            end=start + timedelta(days=4),
            dimensions={INVENTORY_WAREHOUSE_DIMENSION: "W1"},
        )
    )
    assert {movement.dimensions.get(INVENTORY_PRODUCT_DIMENSION) for movement in result} == {
        "P1",
        "P2",
    }
    assert len(result) == 3


def test_inventory_movement_query_filters_by_product_and_warehouse() -> None:
    start = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    persistence = InMemoryRegisterFactPersistence()
    composition = StandardConfigurationBootstrap().compose_inventory_register_platform(persistence)
    documents = []
    for product, warehouse, quantity, offset in (
        ("P1", "W1", "10", 0),
        ("P1", "W2", "20", 1),
        ("P2", "W1", "30", 2),
        ("P1", "W1", "5", 3),
    ):
        _persistence, document, _state, _engine, _composition = post_goods_receipt(
            product=product,
            warehouse=warehouse,
            quantity=quantity,
            accounting_time=start + timedelta(days=offset),
            persistence=persistence,
            composition=composition,
        )
        documents.append(document)

    result = composition.movement_query.query(
        make_query(
            start=start - timedelta(hours=1),
            end=start + timedelta(days=4),
            dimensions={
                INVENTORY_PRODUCT_DIMENSION: "P1",
                INVENTORY_WAREHOUSE_DIMENSION: "W1",
            },
        )
    )
    assert {movement.source_document_identity for movement in result} == {
        documents[0].identity,
        documents[3].identity,
    }


def test_inventory_movement_query_filters_by_accounting_period() -> None:
    start = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    persistence = InMemoryRegisterFactPersistence()
    composition = StandardConfigurationBootstrap().compose_inventory_register_platform(persistence)
    for product, offset in (("P1", 0), ("P1", 1), ("P2", 2)):
        post_goods_receipt(
            product=product,
            warehouse="W1",
            quantity="10",
            accounting_time=start + timedelta(days=offset),
            persistence=persistence,
            composition=composition,
        )

    result = composition.movement_query.query(
        make_query(
            start=start + timedelta(days=1),
            end=start + timedelta(days=3),
        )
    )
    assert len(result) == 2
    assert {movement.accounting_time for movement in result} == {
        start + timedelta(days=1),
        start + timedelta(days=2),
    }


def test_inventory_movement_query_uses_half_open_period() -> None:
    start = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    end = start + timedelta(days=2)
    persistence = InMemoryRegisterFactPersistence()
    composition = StandardConfigurationBootstrap().compose_inventory_register_platform(persistence)
    for offset in (0, 1, 2):
        post_goods_receipt(
            product="P1",
            warehouse="W1",
            quantity="10",
            accounting_time=start + timedelta(days=offset),
            persistence=persistence,
            composition=composition,
        )

    result = composition.movement_query.query(make_query(start=start, end=end))
    assert {movement.accounting_time for movement in result} == {
        start,
        start + timedelta(days=1),
    }


def test_inventory_movement_query_combines_period_and_dimensions() -> None:
    start = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    persistence = InMemoryRegisterFactPersistence()
    composition = StandardConfigurationBootstrap().compose_inventory_register_platform(persistence)
    for product, warehouse, offset in (
        ("P1", "W1", 0),
        ("P1", "W2", 1),
        ("P1", "W1", 2),
        ("P2", "W1", 1),
    ):
        post_goods_receipt(
            product=product,
            warehouse=warehouse,
            quantity="10",
            accounting_time=start + timedelta(days=offset),
            persistence=persistence,
            composition=composition,
        )

    result = composition.movement_query.query(
        make_query(
            start=start + timedelta(days=1),
            end=start + timedelta(days=3),
            dimensions={
                INVENTORY_PRODUCT_DIMENSION: "P1",
                INVENTORY_WAREHOUSE_DIMENSION: "W1",
            },
        )
    )
    assert len(result) == 1
    assert result[0].accounting_time == start + timedelta(days=2)


def test_inventory_persisted_movements_match_current_totals_and_balance() -> None:
    start = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    persistence = InMemoryRegisterFactPersistence()
    composition = StandardConfigurationBootstrap().compose_inventory_register_platform(persistence)
    for product, warehouse, quantity, offset in (
        ("P1", "W1", "10", 0),
        ("P1", "W2", "20", 1),
        ("P2", "W1", "30", 2),
        ("P1", "W1", "5", 3),
    ):
        post_goods_receipt(
            product=product,
            warehouse=warehouse,
            quantity=quantity,
            accounting_time=start + timedelta(days=offset),
            persistence=persistence,
            composition=composition,
        )

    assert_inventory_consistency(
        persistence=persistence,
        composition=composition,
        product="P1",
        warehouse="W1",
    )
