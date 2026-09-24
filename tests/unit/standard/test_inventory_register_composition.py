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
from accore.platform.posting import (
    MappingPostingHandlerResolver,
    PostingContextFactory,
    PostingEngine,
    PostingOutcome,
    PostingServices,
)
from accore.platform.registers import BalanceQuery, TotalsKey
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


class FixedClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def now(self) -> datetime:
        return self.value


class InMemoryPersistence:
    def __init__(self) -> None:
        self.movements = {}

    def append(self, movements) -> None:
        for movement in movements:
            self.movements[movement.identity] = movement

    def find_by_source_document(self, register_identity, source_document_identity):
        return tuple(
            movement
            for movement in self.movements.values()
            if movement.register_identity == register_identity
            and movement.source_document_identity == source_document_identity
        )

    def remove(self, movement_identities) -> None:
        for identity in movement_identities:
            self.movements.pop(identity, None)

    def enumerate(self, register_identity):
        return tuple(
            movement
            for movement in self.movements.values()
            if movement.register_identity == register_identity
        )


def make_document() -> ObjectInstance:
    configuration = ActiveConfiguration(
        identity=ConfigurationIdentity("test"),
        version=ConfigurationVersion(1),
        published_metadata=__import__(
            "accore.platform.metadata", fromlist=["PublishedMetadataView"]
        ).PublishedMetadataView(()),
    )
    return ObjectInstance(
        Identifier.new(),
        FakeObjectType(Identifier.new()),
        ObjectContext(RuntimeConfigurationContext(configuration)),
    )


def make_state(quantity: str) -> RuntimeDurableState:
    return RuntimeDurableState(
        fields=DurableFieldState(
            {
                "lines": CollectionValue(
                    (
                        StructuredValue(
                            {
                                INVENTORY_PRODUCT_DIMENSION: "P1",
                                INVENTORY_WAREHOUSE_DIMENSION: "W1",
                                INVENTORY_QUANTITY_RESOURCE: Decimal(quantity),
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


class StateProvider:
    def __init__(self, state: RuntimeDurableState) -> None:
        self.state = state

    def get(self, document: ObjectInstance) -> RuntimeDurableState:
        return self.state


def build_engine(
    persistence: InMemoryPersistence, document: ObjectInstance
) -> tuple[PostingEngine, object]:
    composition = StandardConfigurationBootstrap().compose_inventory_register_platform(persistence)
    resolver = MappingPostingHandlerResolver(
        {document.object_type.metadata_identity(): GoodsReceiptPostingHandler()}
    )
    services = PostingServices(StateProvider(make_state("2.5")))
    engine = PostingEngine(
        resolver,
        PostingContextFactory(services, FixedClock(datetime(2026, 9, 24, 12, 0, tzinfo=UTC))),
        composition.movement_validator,
        composition.posting_result_coordinator,
    )
    return engine, composition


def test_standard_bootstrap_composes_inventory_over_generic_register_platform() -> None:
    persistence = InMemoryPersistence()
    document = make_document()
    engine, composition = build_engine(persistence, document)

    assert composition.maintenance.state(INVENTORY_REGISTER_ID).lifecycle.value == "active"
    assert composition.maintenance.state(INVENTORY_REGISTER_ID).consistency.value == "valid"

    result = engine.post(document)

    assert result.outcome is PostingOutcome.SUCCESS
    assert len(persistence.movements) == 1
    movement = next(iter(persistence.movements.values()))
    assert movement.register_identity == INVENTORY_REGISTER_ID
    assert composition.balance_query.query(
        BalanceQuery(
            register_identity=INVENTORY_REGISTER_ID,
            aggregation_scope=TotalsKey.from_mapping(
                {
                    INVENTORY_PRODUCT_DIMENSION: "P1",
                    INVENTORY_WAREHOUSE_DIMENSION: "W1",
                }
            ),
        )
    ).value == Decimal("2.5")


def test_standard_bootstrap_composition_unpost_removes_fact_and_total() -> None:
    persistence = InMemoryPersistence()
    document = make_document()
    engine, composition = build_engine(persistence, document)

    assert engine.post(document).outcome is PostingOutcome.SUCCESS
    assert engine.unpost(document).outcome is PostingOutcome.SUCCESS
    assert persistence.movements == {}
    assert composition.balance_query.query(
        BalanceQuery(
            register_identity=INVENTORY_REGISTER_ID,
            aggregation_scope=TotalsKey.from_mapping(
                {
                    INVENTORY_PRODUCT_DIMENSION: "P1",
                    INVENTORY_WAREHOUSE_DIMENSION: "W1",
                }
            ),
        )
    ).value == Decimal(0)


def test_standard_bootstrap_composition_repost_replaces_persisted_effect() -> None:
    persistence = InMemoryPersistence()
    document = make_document()
    engine, _composition = build_engine(persistence, document)

    assert engine.post(document).outcome is PostingOutcome.SUCCESS
    old_identity = next(iter(persistence.movements))
    old_movement = persistence.movements[old_identity]

    assert engine.repost(document).outcome is PostingOutcome.SUCCESS

    assert len(persistence.movements) == 1

    new_identity = next(iter(persistence.movements))
    new_movement = persistence.movements[new_identity]

    assert new_movement == old_movement
