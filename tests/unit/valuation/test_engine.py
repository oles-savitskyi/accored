from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from accore.platform.foundation import Identifier
from accore.platform.posting import MovementSet
from accore.platform.registers import (
    Movement,
    MovementAttributes,
    MovementDimensions,
    MovementResources,
    MovementType,
)
from accore.platform.valuation import (
    ConsumptionPlan,
    FIFOValuationMethod,
    LayerEstablishmentPlan,
    PersistedLayerReference,
    PlannedLayerReference,
    ValuationEngine,
    ValuationInput,
    ValuationInsufficientQuantityError,
    ValuationKey,
    ValuationLayer,
    ValuationValidationError,
)


class FakeValuationInputProvider:
    def provide(self, movement: Movement) -> ValuationInput:
        from accore.platform.valuation import ValuationValidationError

        product = movement.dimensions.get("product")
        warehouse = movement.dimensions.get("warehouse")
        quantity = movement.resources.get("quantity")
        if not isinstance(product, str) or not isinstance(warehouse, str):
            raise ValuationValidationError("Invalid valuation dimensions")
        if not isinstance(quantity, Decimal) or quantity <= 0:
            raise ValuationValidationError("requires a positive Decimal quantity")
        if movement.accounting_time is None:
            raise ValuationValidationError("requires accounting_time")
        return ValuationInput(
            valuation_key=ValuationKey({"product": product, "warehouse": warehouse}),
            quantity=quantity,
            document_identity=movement.source_document_identity,
            source_identity=movement.identity,
            occurred_at=movement.accounting_time,
        )


def engine(reader: FakeLayerReader) -> ValuationEngine:
    return ValuationEngine(FakeValuationInputProvider(), reader, FIFOValuationMethod())


@dataclass
class FakeLayerReader:
    layers: dict[ValuationKey, tuple[ValuationLayer, ...]]
    calls: list[ValuationKey]

    def find_available_layers(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[ValuationLayer, ...]:
        self.calls.append(valuation_key)
        return self.layers.get(valuation_key, ())


def movement(
    movement_type: MovementType,
    *,
    quantity: str = "5",
    product: str = "PR-01",
    warehouse: str = "WH-01",
    accounting_time: datetime | None = None,
    source_document_identity: Identifier | None = None,
) -> Movement:
    return Movement(
        identity=Identifier.new(),
        source_document_identity=source_document_identity or Identifier.new(),
        register_identity=Identifier.new(),
        movement_type=movement_type,
        dimensions=MovementDimensions.from_mapping({"product": product, "warehouse": warehouse}),
        resources=MovementResources.from_mapping({"quantity": Decimal(quantity)}),
        attributes=MovementAttributes.from_mapping({}),
        accounting_time=accounting_time or datetime(2026, 9, 25, 15, 0, tzinfo=UTC),
    )


def layer(
    key: ValuationKey,
    *,
    quantity: str,
    cost: str,
    created_at: datetime,
) -> ValuationLayer:
    return ValuationLayer(
        identity=Identifier.new(),
        valuation_key=key,
        quantity=Decimal(quantity),
        total_cost=Decimal(cost),
        source_document_identity=Identifier.new(),
        source_movement_identity=Identifier.new(),
        created_at=created_at,
    )


def test_prepare_income_creates_layer_establishment_plan() -> None:
    income = movement(MovementType.INCOME, quantity="7")
    reader = FakeLayerReader({}, [])

    plan = engine(reader).prepare(MovementSet((income,)))

    assert reader.calls == []
    assert len(plan.operations) == 1
    operation = plan.operations[0]
    assert isinstance(operation, LayerEstablishmentPlan)
    assert isinstance(operation.reference, PlannedLayerReference)
    assert operation.valuation_key == ValuationKey({"product": "PR-01", "warehouse": "WH-01"})
    assert operation.quantity == Decimal(7)
    assert operation.source_document_identity == income.source_document_identity
    assert operation.source_movement_identity == income.identity
    assert operation.source_document_identity == income.source_document_identity
    assert plan.document_identity == income.source_document_identity
    assert operation.created_at == income.accounting_time


def test_prepare_expense_reads_layers_and_creates_consumption_plan() -> None:
    expense = movement(MovementType.EXPENSE, quantity="4")
    key = ValuationKey({"product": "PR-01", "warehouse": "WH-01"})
    assert expense.accounting_time is not None

    existing_layer = layer(
        key,
        quantity="10",
        cost="100",
        created_at=expense.accounting_time - timedelta(days=1),
    )
    reader = FakeLayerReader({key: (existing_layer,)}, [])

    plan = engine(reader).prepare(MovementSet((expense,)))

    assert reader.calls == [key]
    assert len(plan.operations) == 1
    operation = plan.operations[0]
    assert isinstance(operation, ConsumptionPlan)
    assert operation.valuation_key == key
    assert isinstance(operation.layer_reference, PersistedLayerReference)
    assert operation.layer_reference.identity == existing_layer.identity
    assert operation.quantity == Decimal(4)
    assert operation.cost == Decimal(40)
    assert operation.source_identity == expense.identity
    assert operation.document_identity == expense.source_document_identity
    assert plan.document_identity == expense.source_document_identity
    assert operation.created_at == expense.accounting_time


def test_prepare_preserves_movement_order() -> None:
    timestamp = datetime(2026, 9, 25, 15, 0, tzinfo=UTC)
    document_identity = Identifier.new()
    first = movement(
        MovementType.INCOME,
        quantity="2",
        accounting_time=timestamp,
        source_document_identity=document_identity,
    )
    second = movement(
        MovementType.INCOME,
        quantity="3",
        product="PR-02",
        accounting_time=timestamp + timedelta(seconds=1),
        source_document_identity=document_identity,
    )

    plan = engine(FakeLayerReader({}, [])).prepare(MovementSet((first, second)))

    assert plan.document_identity == document_identity
    assert [operation.quantity for operation in plan.operations] == [Decimal(2), Decimal(3)]
    assert [
        operation.source_movement_identity
        for operation in plan.operations
        if isinstance(operation, LayerEstablishmentPlan)
    ] == [first.identity, second.identity]


def test_prepare_reuses_reader_result_and_consumes_remaining_layers_for_multiple_expenses() -> None:
    document_identity = Identifier.new()
    first = movement(MovementType.EXPENSE, quantity="6", source_document_identity=document_identity)
    second = movement(
        MovementType.EXPENSE, quantity="3", source_document_identity=document_identity
    )
    key = ValuationKey({"product": "PR-01", "warehouse": "WH-01"})
    assert first.accounting_time is not None
    existing_layer = layer(
        key,
        quantity="10",
        cost="100",
        created_at=first.accounting_time - timedelta(days=1),
    )
    reader = FakeLayerReader({key: (existing_layer,)}, [])

    plan = engine(reader).prepare(MovementSet((first, second)))

    assert reader.calls == [key]
    assert [operation.quantity for operation in plan.operations] == [
        Decimal(6),
        Decimal(3),
    ]
    operations = plan.operations
    assert all(isinstance(operation, ConsumptionPlan) for operation in operations)
    consumptions = tuple(
        operation for operation in plan.operations if isinstance(operation, ConsumptionPlan)
    )

    assert len(consumptions) == 2
    assert [operation.quantity for operation in consumptions] == [
        Decimal(6),
        Decimal(3),
    ]
    assert [operation.cost for operation in consumptions] == [
        Decimal(60),
        Decimal(30),
    ]


def test_prepare_fails_without_sufficient_layers() -> None:
    expense = movement(MovementType.EXPENSE, quantity="11")
    key = ValuationKey({"product": "PR-01", "warehouse": "WH-01"})
    assert expense.accounting_time is not None
    reader = FakeLayerReader(
        {
            key: (
                layer(
                    key,
                    quantity="10",
                    cost="100",
                    created_at=expense.accounting_time - timedelta(days=1),
                ),
            )
        },
        [],
    )

    with pytest.raises(ValuationInsufficientQuantityError):
        engine(reader).prepare(MovementSet((expense,)))


def test_input_provider_rejects_non_positive_quantity() -> None:
    invalid = movement(MovementType.INCOME, quantity="0")

    with pytest.raises(ValuationValidationError, match="positive Decimal"):
        engine(FakeLayerReader({}, [])).prepare(MovementSet((invalid,)))


def test_input_provider_rejects_missing_accounting_time() -> None:
    invalid = movement(MovementType.INCOME, accounting_time=None)
    object.__setattr__(invalid, "accounting_time", None)

    with pytest.raises(ValuationValidationError, match="accounting_time"):
        engine(FakeLayerReader({}, [])).prepare(MovementSet((invalid,)))


def test_input_provider_rejects_non_string_dimensions() -> None:
    invalid = movement(MovementType.INCOME)
    invalid_dimensions = MovementDimensions.from_mapping({"product": "PR-01", "warehouse": 123})
    object.__setattr__(invalid, "dimensions", invalid_dimensions)

    with pytest.raises(ValuationValidationError, match="Invalid valuation dimensions"):
        engine(FakeLayerReader({}, [])).prepare(MovementSet((invalid,)))


def test_prepare_income_then_expense_references_planned_layer() -> None:
    document_identity = Identifier.new()
    income = movement(
        MovementType.INCOME, quantity="10", source_document_identity=document_identity
    )
    expense = movement(
        MovementType.EXPENSE, quantity="4", source_document_identity=document_identity
    )
    reader = FakeLayerReader({}, [])

    plan = engine(reader).prepare(MovementSet((income, expense)))

    assert len(plan.operations) == 2
    layer_plan = plan.operations[0]
    consumption_plan = plan.operations[1]
    assert isinstance(layer_plan, LayerEstablishmentPlan)
    assert isinstance(consumption_plan, ConsumptionPlan)
    assert isinstance(consumption_plan.layer_reference, PlannedLayerReference)
    assert consumption_plan.layer_reference == layer_plan.reference
    assert consumption_plan.quantity == Decimal(4)
    assert consumption_plan.cost == Decimal(0)
    assert reader.calls == []


def test_valuation_input_is_pure_semantic_input() -> None:
    source = movement(MovementType.INCOME, quantity="3")
    assert source.accounting_time is not None

    value = ValuationInput(
        valuation_key=ValuationKey({"product": "PR-01", "warehouse": "WH-01"}),
        quantity=Decimal(3),
        document_identity=source.source_document_identity,
        source_identity=source.identity,
        occurred_at=source.accounting_time,
    )

    assert value.quantity == Decimal(3)
    assert value.document_identity == source.source_document_identity
    assert value.source_identity == source.identity
    assert value.occurred_at == source.accounting_time
    assert not hasattr(value, "layers")
