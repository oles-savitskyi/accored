from datetime import UTC, datetime
from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.persistence import PersistenceError, PersistenceIndeterminateError
from accore.platform.posting import PostingAPI
from accore.platform.registers import MovementType
from accore.platform.runtime import (
    BusinessStateSnapshot,
    DurableFieldState,
    DurableReferenceState,
    DurableSystemFieldState,
    RuntimeDurableState,
)
from accore.platform.value import CollectionValue, StructuredValue
from standard.posting.goods_receipt import INVENTORY_REGISTER_ID


class FakeObjectType:
    def __init__(self, identity: Identifier) -> None:
        self._identity = identity

    def metadata_identity(self) -> Identifier:
        return self._identity


def make_goods_receipt(
    *,
    product: str,
    warehouse: str,
    quantity: str,
):
    """
    Build the smallest Goods Receipt representation required by
    the Phase 6 vertical slice.

    The exact construction of the ObjectInstance should be aligned
    with the current Standard Configuration API if it differs.
    """
    from accore.platform.configuration import (
        ActiveConfiguration,
        ConfigurationIdentity,
        ConfigurationVersion,
        RuntimeConfigurationContext,
    )
    from accore.platform.metadata.publication import PublishedMetadataView
    from accore.platform.object import (
        ObjectContext,
        ObjectInstance,
    )

    configuration = ActiveConfiguration(
        identity=ConfigurationIdentity("test"),
        version=ConfigurationVersion(1),
        published_metadata=PublishedMetadataView(()),
    )

    context = ObjectContext(RuntimeConfigurationContext(configuration))

    return ObjectInstance(
        Identifier.new(),
        FakeObjectType(Identifier.new()),
        context,
    )


def make_goods_receipt_state(
    *,
    product: str,
    warehouse: str,
    quantity: str,
) -> RuntimeDurableState:
    line = StructuredValue(
        {
            "product": product,
            "warehouse": warehouse,
            "quantity": Decimal(quantity),
        }
    )

    return RuntimeDurableState(
        fields=DurableFieldState(
            {
                "lines": CollectionValue((line,)),
            }
        ),
        references=DurableReferenceState.empty(),
        business_state=BusinessStateSnapshot.empty(),
        system_fields=DurableSystemFieldState.empty(),
    )


class FixedClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def now(self) -> datetime:
        return self.value


class StateProvider:
    def __init__(self, states: dict[Identifier, RuntimeDurableState]) -> None:
        self.states = states

    def get(self, document):
        return self.states[document.identity]


class InventoryRegisterContractResolver:
    def resolve(self, register_identity: Identifier):
        if register_identity != INVENTORY_REGISTER_ID:
            raise KeyError(register_identity)

        from standard.posting.inventory import (
            InventoryRegisterPostingContract,
        )

        return InventoryRegisterPostingContract()


class InMemoryPostingResultCoordinator:
    def __init__(self) -> None:
        self.effects: dict[Identifier, tuple] = {}

    def establish(self, document, movement_set) -> None:
        self.effects[document.identity] = tuple(movement_set.movements)

    def remove(self, document) -> None:
        self.effects.pop(document.identity, None)

    def movements_for(self, document):
        return self.effects.get(document.identity, ())


class RecordingPostingEventPublisher:
    def __init__(self) -> None:
        self.events = []

    def publish(self, event) -> None:
        self.events.append(event)


class FailingPostingResultCoordinator(InMemoryPostingResultCoordinator):
    def __init__(self, error: Exception) -> None:
        super().__init__()
        self.error = error

    def establish(self, document, movement_set) -> None:
        raise self.error


def make_posting_api(
    *,
    document,
    state_provider: StateProvider,
    clock: FixedClock,
    coordinator: InMemoryPostingResultCoordinator,
    event_publisher=None,
) -> PostingAPI:
    from accore.platform.posting import (
        MappingPostingHandlerResolver,
        PostingContextFactory,
        PostingEngine,
        PostingServices,
    )
    from accore.platform.registers import DefaultMovementValidator
    from standard.posting.goods_receipt import GoodsReceiptPostingHandler

    handler = GoodsReceiptPostingHandler()
    handler_resolver = MappingPostingHandlerResolver(
        {document.object_type.metadata_identity(): handler}
    )
    services = PostingServices(document_state=state_provider)
    context_factory = PostingContextFactory(services=services, clock=clock)
    movement_validator = DefaultMovementValidator(
        InventoryRegisterContractResolver(),
    )
    return PostingEngine(
        handler_resolver=handler_resolver,
        context_factory=context_factory,
        movement_validator=movement_validator,
        result_coordinator=coordinator,
        event_publisher=event_publisher,
    )


def test_goods_receipt_posting_vertical_slice() -> None:
    """
    Full Phase 6 vertical slice:

        Goods Receipt
            -> PostingAPI
            -> Posting Engine
            -> Posting Context
            -> Goods Receipt Handler
            -> MovementSet
            -> Inventory Register Contract
            -> Required Persistent Accounting Result
    """
    document = make_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="2.5",
    )

    state_provider = StateProvider(
        {
            document.identity: make_goods_receipt_state(
                product="P1",
                warehouse="W1",
                quantity="2.5",
            )
        }
    )

    accounting_time = datetime(2026, 9, 17, 10, 30, 0, tzinfo=UTC)
    clock = FixedClock(accounting_time)
    coordinator = InMemoryPostingResultCoordinator()

    posting_api = make_posting_api(
        document=document,
        state_provider=state_provider,
        clock=clock,
        coordinator=coordinator,
    )

    result = posting_api.post(document)

    assert result.is_success
    assert result.error is None

    movements = coordinator.movements_for(document)

    assert len(movements) == 1

    movement = movements[0]

    assert movement.source_document_identity == document.identity
    assert movement.register_identity == INVENTORY_REGISTER_ID
    assert movement.movement_type is MovementType.INCOME

    assert movement.dimensions.get("product") == "P1"
    assert movement.dimensions.get("warehouse") == "W1"

    assert movement.resources.get("quantity") == Decimal("2.5")
    assert movement.accounting_time == accounting_time


def test_empty_goods_receipt_vertical_slice_fails_without_effect() -> None:
    """
    An empty Goods Receipt must fail through the public Posting API
    and must not establish an Inventory accounting result.
    """
    document = make_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="2.5",
    )

    state_provider = StateProvider(
        {
            document.identity: RuntimeDurableState(
                fields=DurableFieldState(
                    {
                        "lines": CollectionValue(()),
                    }
                ),
                references=DurableReferenceState.empty(),
                business_state=BusinessStateSnapshot.empty(),
                system_fields=DurableSystemFieldState.empty(),
            )
        }
    )

    accounting_time = datetime(2026, 9, 17, 10, 30, 0, tzinfo=UTC)
    clock = FixedClock(accounting_time)
    coordinator = InMemoryPostingResultCoordinator()

    posting_api = make_posting_api(
        document=document,
        state_provider=state_provider,
        clock=clock,
        coordinator=coordinator,
    )

    result = posting_api.post(document)

    assert result.is_failure
    assert not result.is_success
    assert result.error is not None

    assert coordinator.movements_for(document) == ()


def test_goods_receipt_repost_vertical_slice_replaces_old_effect() -> None:
    """
    Reposting must rebuild the Inventory accounting effect from the
    current Goods Receipt state rather than accumulating the previous
    posting result.
    """
    document = make_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="2.5",
    )

    state_provider = StateProvider(
        {
            document.identity: make_goods_receipt_state(
                product="P1",
                warehouse="W1",
                quantity="2.5",
            )
        }
    )

    accounting_time = datetime(2026, 9, 17, 10, 30, 0, tzinfo=UTC)
    clock = FixedClock(accounting_time)
    coordinator = InMemoryPostingResultCoordinator()

    posting_api = make_posting_api(
        document=document,
        state_provider=state_provider,
        clock=clock,
        coordinator=coordinator,
    )

    first_result = posting_api.post(document)

    assert first_result.is_success

    first_movements = coordinator.movements_for(document)

    assert len(first_movements) == 1
    assert first_movements[0].resources.get("quantity") == Decimal("2.5")

    state_provider.states[document.identity] = make_goods_receipt_state(
        product="P1",
        warehouse="W1",
        quantity="7.0",
    )

    repost_result = posting_api.repost(document)

    assert repost_result.is_success

    reposted_movements = coordinator.movements_for(document)

    assert len(reposted_movements) == 1

    movement = reposted_movements[0]

    assert movement.source_document_identity == document.identity
    assert movement.register_identity == INVENTORY_REGISTER_ID
    assert movement.movement_type is MovementType.INCOME
    assert movement.dimensions.get("product") == "P1"
    assert movement.dimensions.get("warehouse") == "W1"
    assert movement.resources.get("quantity") == Decimal("7.0")
    assert movement.accounting_time == accounting_time


import pytest


@pytest.mark.parametrize(
    ("state", "description"),
    [
        (
            RuntimeDurableState(
                fields=DurableFieldState(
                    {
                        "lines": CollectionValue(
                            (
                                StructuredValue(
                                    {
                                        "warehouse": "W1",
                                        "quantity": Decimal("2.5"),
                                    }
                                ),
                            )
                        ),
                    }
                ),
                references=DurableReferenceState.empty(),
                business_state=BusinessStateSnapshot.empty(),
                system_fields=DurableSystemFieldState.empty(),
            ),
            "missing Product",
        ),
        (
            RuntimeDurableState(
                fields=DurableFieldState(
                    {
                        "lines": CollectionValue(
                            (
                                StructuredValue(
                                    {
                                        "product": "P1",
                                        "quantity": Decimal("2.5"),
                                    }
                                ),
                            )
                        ),
                    }
                ),
                references=DurableReferenceState.empty(),
                business_state=BusinessStateSnapshot.empty(),
                system_fields=DurableSystemFieldState.empty(),
            ),
            "missing Warehouse",
        ),
        (
            RuntimeDurableState(
                fields=DurableFieldState(
                    {
                        "lines": CollectionValue(
                            (
                                StructuredValue(
                                    {
                                        "product": "P1",
                                        "warehouse": "W1",
                                        "quantity": "2.5",
                                    }
                                ),
                            )
                        ),
                    }
                ),
                references=DurableReferenceState.empty(),
                business_state=BusinessStateSnapshot.empty(),
                system_fields=DurableSystemFieldState.empty(),
            ),
            "invalid Quantity type",
        ),
        (
            RuntimeDurableState(
                fields=DurableFieldState(
                    {
                        "lines": CollectionValue(
                            (
                                StructuredValue(
                                    {
                                        "product": "P1",
                                        "warehouse": "W1",
                                        "quantity": Decimal(0),
                                    }
                                ),
                            )
                        ),
                    }
                ),
                references=DurableReferenceState.empty(),
                business_state=BusinessStateSnapshot.empty(),
                system_fields=DurableSystemFieldState.empty(),
            ),
            "non-positive Quantity",
        ),
        (
            RuntimeDurableState(
                fields=DurableFieldState(
                    {
                        "lines": CollectionValue((Decimal("2.5"),)),
                    }
                ),
                references=DurableReferenceState.empty(),
                business_state=BusinessStateSnapshot.empty(),
                system_fields=DurableSystemFieldState.empty(),
            ),
            "invalid line representation",
        ),
        (
            RuntimeDurableState(
                fields=DurableFieldState({}),
                references=DurableReferenceState.empty(),
                business_state=BusinessStateSnapshot.empty(),
                system_fields=DurableSystemFieldState.empty(),
            ),
            "missing Lines collection",
        ),
    ],
)
def test_invalid_goods_receipt_line_fails_without_accounting_effect(
    state: RuntimeDurableState,
    description: str,
) -> None:
    """Invalid Goods Receipt input must fail through the public Posting API."""
    document = make_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="2.5",
    )

    state_provider = StateProvider(
        {
            document.identity: state,
        }
    )

    accounting_time = datetime(2026, 9, 17, 10, 30, 0, tzinfo=UTC)
    clock = FixedClock(accounting_time)
    coordinator = InMemoryPostingResultCoordinator()

    posting_api = make_posting_api(
        document=document,
        state_provider=state_provider,
        clock=clock,
        coordinator=coordinator,
    )

    result = posting_api.post(document)

    assert result.is_failure, description
    assert not result.is_success
    assert result.error is not None

    assert coordinator.movements_for(document) == ()


@pytest.mark.parametrize(
    ("persistence_error", "expected_indeterminate"),
    [
        (PersistenceError("known persistence failure"), False),
        (
            PersistenceIndeterminateError("indeterminate persistence outcome"),
            True,
        ),
    ],
)
def test_persistence_outcome_is_preserved_by_posting_api(
    persistence_error: Exception,
    expected_indeterminate: bool,
) -> None:
    """Posting preserves known and indeterminate persistence outcomes."""
    document = make_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="2.5",
    )

    state = make_goods_receipt_state(
        product="P1",
        warehouse="W1",
        quantity="2.5",
    )
    state_provider = StateProvider({document.identity: state})

    accounting_time = datetime(2026, 9, 17, 10, 30, 0, tzinfo=UTC)
    clock = FixedClock(accounting_time)

    coordinator = FailingPostingResultCoordinator(persistence_error)

    posting_api = make_posting_api(
        document=document,
        state_provider=state_provider,
        clock=clock,
        coordinator=coordinator,
    )

    result = posting_api.post(document)

    if expected_indeterminate:
        assert result.is_indeterminate
        assert not result.is_failure
        assert not result.is_success
    else:
        assert result.is_failure
        assert not result.is_indeterminate
        assert not result.is_success

    assert result.error is not None
    assert coordinator.movements_for(document) == ()


from accore.platform.posting import DocumentPosted


def test_successful_post_publishes_document_posted() -> None:
    document = make_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="2.5",
    )
    state_provider = StateProvider(
        {
            document.identity: make_goods_receipt_state(
                product="P1",
                warehouse="W1",
                quantity="2.5",
            )
        }
    )
    clock = FixedClock(datetime(2026, 9, 17, 10, 30, 0, tzinfo=UTC))
    coordinator = InMemoryPostingResultCoordinator()
    events = RecordingPostingEventPublisher()

    posting_api = make_posting_api(
        document=document,
        state_provider=state_provider,
        clock=clock,
        coordinator=coordinator,
        event_publisher=events,
    )

    result = posting_api.post(document)

    assert result.is_success
    assert len(events.events) == 1
    assert isinstance(events.events[0], DocumentPosted)
    assert events.events[0].document_identity == document.identity


def test_failed_post_does_not_publish_document_posted() -> None:
    document = make_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="2.5",
    )
    state_provider = StateProvider(
        {
            document.identity: make_goods_receipt_state(
                product="P1",
                warehouse="W1",
                quantity="2.5",
            )
        }
    )
    clock = FixedClock(datetime(2026, 9, 17, 10, 30, 0, tzinfo=UTC))
    coordinator = FailingPostingResultCoordinator(PersistenceError("known persistence failure"))
    events = RecordingPostingEventPublisher()

    posting_api = make_posting_api(
        document=document,
        state_provider=state_provider,
        clock=clock,
        coordinator=coordinator,
        event_publisher=events,
    )

    result = posting_api.post(document)

    assert result.is_failure
    assert events.events == []


from accore.platform.posting import DocumentUnposted


def test_successful_unpost_publishes_document_unposted() -> None:
    document = make_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="2.5",
    )
    state_provider = StateProvider(
        {
            document.identity: make_goods_receipt_state(
                product="P1",
                warehouse="W1",
                quantity="2.5",
            )
        }
    )
    clock = FixedClock(datetime(2026, 9, 17, 10, 30, 0, tzinfo=UTC))
    coordinator = InMemoryPostingResultCoordinator()
    events = RecordingPostingEventPublisher()

    posting_api = make_posting_api(
        document=document,
        state_provider=state_provider,
        clock=clock,
        coordinator=coordinator,
        event_publisher=events,
    )

    post_result = posting_api.post(document)
    assert post_result.is_success
    assert len(coordinator.movements_for(document)) == 1

    events.events.clear()

    unpost_result = posting_api.unpost(document)

    assert unpost_result.is_success
    assert coordinator.movements_for(document) == ()
    assert len(events.events) == 1
    assert isinstance(events.events[0], DocumentUnposted)
    assert events.events[0].document_identity == document.identity


from accore.platform.posting import DocumentReposted


def test_successful_repost_publishes_document_reposted() -> None:
    document = make_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="2.5",
    )
    state_provider = StateProvider(
        {
            document.identity: make_goods_receipt_state(
                product="P1",
                warehouse="W1",
                quantity="2.5",
            )
        }
    )
    clock = FixedClock(datetime(2026, 9, 17, 10, 30, 0, tzinfo=UTC))
    coordinator = InMemoryPostingResultCoordinator()
    events = RecordingPostingEventPublisher()

    posting_api = make_posting_api(
        document=document,
        state_provider=state_provider,
        clock=clock,
        coordinator=coordinator,
        event_publisher=events,
    )

    post_result = posting_api.post(document)
    assert post_result.is_success

    state_provider.states[document.identity] = make_goods_receipt_state(
        product="P1",
        warehouse="W1",
        quantity="7.0",
    )

    events.events.clear()

    repost_result = posting_api.repost(document)

    assert repost_result.is_success
    assert len(events.events) == 1
    assert isinstance(events.events[0], DocumentReposted)
    assert events.events[0].document_identity == document.identity

    movements = coordinator.movements_for(document)
    assert len(movements) == 1
    assert movements[0].resources.get("quantity") == Decimal("7.0")


def test_unpost_removes_inventory_accounting_effect() -> None:
    document = make_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="2.5",
    )
    state_provider = StateProvider(
        {
            document.identity: make_goods_receipt_state(
                product="P1",
                warehouse="W1",
                quantity="2.5",
            )
        }
    )
    clock = FixedClock(datetime(2026, 9, 17, 10, 30, 0, tzinfo=UTC))
    coordinator = InMemoryPostingResultCoordinator()

    posting_api = make_posting_api(
        document=document,
        state_provider=state_provider,
        clock=clock,
        coordinator=coordinator,
    )

    post_result = posting_api.post(document)

    assert post_result.is_success

    movements = coordinator.movements_for(document)
    assert len(movements) == 1
    assert movements[0].resources.get("quantity") == Decimal("2.5")

    unpost_result = posting_api.unpost(document)

    assert unpost_result.is_success
    assert coordinator.movements_for(document) == ()


def test_repost_known_persistence_failure_is_failure() -> None:
    document = make_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="2.5",
    )
    state_provider = StateProvider(
        {
            document.identity: make_goods_receipt_state(
                product="P1",
                warehouse="W1",
                quantity="2.5",
            )
        }
    )
    clock = FixedClock(datetime(2026, 9, 17, 10, 30, 0, tzinfo=UTC))

    initial_coordinator = InMemoryPostingResultCoordinator()
    posting_api = make_posting_api(
        document=document,
        state_provider=state_provider,
        clock=clock,
        coordinator=initial_coordinator,
    )

    post_result = posting_api.post(document)

    assert post_result.is_success
    assert len(initial_coordinator.movements_for(document)) == 1

    state_provider.states[document.identity] = make_goods_receipt_state(
        product="P1",
        warehouse="W1",
        quantity="7.0",
    )

    failing_coordinator = FailingPostingResultCoordinator(
        PersistenceError("repost persistence failure")
    )
    repost_api = make_posting_api(
        document=document,
        state_provider=state_provider,
        clock=clock,
        coordinator=failing_coordinator,
    )

    repost_result = repost_api.repost(document)

    assert repost_result.is_failure
    assert not repost_result.is_success
    assert not repost_result.is_indeterminate
    assert repost_result.error is not None

    assert failing_coordinator.movements_for(document) == ()


def test_repost_indeterminate_persistence_outcome_is_indeterminate() -> None:
    document = make_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="2.5",
    )
    state_provider = StateProvider(
        {
            document.identity: make_goods_receipt_state(
                product="P1",
                warehouse="W1",
                quantity="2.5",
            )
        }
    )
    clock = FixedClock(datetime(2026, 9, 17, 10, 30, 0, tzinfo=UTC))

    initial_coordinator = InMemoryPostingResultCoordinator()
    posting_api = make_posting_api(
        document=document,
        state_provider=state_provider,
        clock=clock,
        coordinator=initial_coordinator,
    )

    post_result = posting_api.post(document)

    assert post_result.is_success

    state_provider.states[document.identity] = make_goods_receipt_state(
        product="P1",
        warehouse="W1",
        quantity="7.0",
    )

    indeterminate_coordinator = FailingPostingResultCoordinator(
        PersistenceIndeterminateError("repost outcome is unknown")
    )
    repost_api = make_posting_api(
        document=document,
        state_provider=state_provider,
        clock=clock,
        coordinator=indeterminate_coordinator,
    )

    repost_result = repost_api.repost(document)

    assert repost_result.is_indeterminate
    assert not repost_result.is_success
    assert not repost_result.is_failure
    assert repost_result.error is not None

    assert indeterminate_coordinator.movements_for(document) == ()


def make_goods_receipt_state_from_lines(
    lines: tuple[tuple[str, str, str], ...],
) -> RuntimeDurableState:
    values = tuple(
        StructuredValue(
            {
                "product": product,
                "warehouse": warehouse,
                "quantity": Decimal(quantity),
            }
        )
        for product, warehouse, quantity in lines
    )

    return RuntimeDurableState(
        fields=DurableFieldState({"lines": CollectionValue(values)}),
        references=DurableReferenceState.empty(),
        business_state=BusinessStateSnapshot.empty(),
        system_fields=DurableSystemFieldState.empty(),
    )


def test_goods_receipt_multiple_lines_preserve_movement_order() -> None:
    document = make_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="2.5",
    )
    lines = (
        ("P1", "W1", "2.5"),
        ("P2", "W2", "7.0"),
        ("P3", "W3", "1.25"),
    )
    state_provider = StateProvider({document.identity: make_goods_receipt_state_from_lines(lines)})
    clock = FixedClock(datetime(2026, 9, 17, 10, 30, 0, tzinfo=UTC))
    coordinator = InMemoryPostingResultCoordinator()

    posting_api = make_posting_api(
        document=document,
        state_provider=state_provider,
        clock=clock,
        coordinator=coordinator,
    )

    result = posting_api.post(document)

    assert result.is_success

    movements = coordinator.movements_for(document)

    assert len(movements) == len(lines)

    for movement, (product, warehouse, quantity) in zip(
        movements,
        lines,
        strict=True,
    ):
        assert movement.source_document_identity == document.identity
        assert movement.register_identity == INVENTORY_REGISTER_ID
        assert movement.movement_type is MovementType.INCOME
        assert movement.dimensions.get("product") == product
        assert movement.dimensions.get("warehouse") == warehouse
        assert movement.resources.get("quantity") == Decimal(quantity)


def make_equivalent_goods_receipts(
    identity: Identifier,
) -> tuple[object, object]:
    from accore.platform.configuration import (
        ActiveConfiguration,
        ConfigurationIdentity,
        ConfigurationVersion,
        RuntimeConfigurationContext,
    )
    from accore.platform.metadata.publication import PublishedMetadataView
    from accore.platform.object import ObjectContext, ObjectInstance

    configuration = ActiveConfiguration(
        identity=ConfigurationIdentity("test"),
        version=ConfigurationVersion(1),
        published_metadata=PublishedMetadataView(()),
    )
    context = ObjectContext(RuntimeConfigurationContext(configuration))
    object_type = FakeObjectType(Identifier.new())

    first = ObjectInstance(
        identity,
        object_type,
        context,
    )
    second = ObjectInstance(
        identity,
        object_type,
        context,
    )

    return first, second


def test_goods_receipt_posting_is_deterministic_for_equivalent_inputs() -> None:
    document_identity = Identifier.new()
    first_document, second_document = make_equivalent_goods_receipts(document_identity)

    first_state = make_goods_receipt_state(
        product="P1",
        warehouse="W1",
        quantity="2.5",
    )
    second_state = make_goods_receipt_state(
        product="P1",
        warehouse="W1",
        quantity="2.5",
    )

    first_state_provider = StateProvider({first_document.identity: first_state})
    second_state_provider = StateProvider({second_document.identity: second_state})

    accounting_time = datetime(
        2026,
        9,
        17,
        10,
        30,
        0,
        tzinfo=UTC,
    )

    first_coordinator = InMemoryPostingResultCoordinator()
    first_api = make_posting_api(
        document=first_document,
        state_provider=first_state_provider,
        clock=FixedClock(accounting_time),
        coordinator=first_coordinator,
    )

    second_coordinator = InMemoryPostingResultCoordinator()
    second_api = make_posting_api(
        document=second_document,
        state_provider=second_state_provider,
        clock=FixedClock(accounting_time),
        coordinator=second_coordinator,
    )

    first_result = first_api.post(first_document)
    second_result = second_api.post(second_document)

    assert first_result.is_success
    assert second_result.is_success

    first_movements = first_coordinator.movements_for(first_document)
    second_movements = second_coordinator.movements_for(second_document)

    assert first_movements == second_movements
