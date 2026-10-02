from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.registers import (
    DefaultTotalsEngine,
    Movement,
    MovementAttributes,
    MovementDimensions,
    MovementResources,
    MovementType,
)
from accore.platform.reporting import (
    DefaultReportCompiler,
    DefaultReportExecutionPlanBuilder,
    DefaultReportRuntime,
    DefaultReportValidator,
    ReportFilter,
    ReportFilterOperator,
    ReportValue,
)
from accore.platform.valuation import CostMovement, DefaultCostTotalsEngine, ValuationKey
from standard.bootstrap import StandardConfigurationBootstrap
from standard.registers.inventory import inventory_register_configuration
from standard.reporting import (
    INVENTORY_BALANCE_REPORT_DEFINITION,
    INVENTORY_BALANCE_REPORT_IDENTITY,
    INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY,
)


def _state() -> tuple[DefaultTotalsEngine, DefaultCostTotalsEngine]:
    configuration = inventory_register_configuration()
    totals = DefaultTotalsEngine((configuration.totals_definition,))
    cost_totals = DefaultCostTotalsEngine()
    return totals, cost_totals


def _add_inventory_state(
    totals: DefaultTotalsEngine,
    cost_totals: DefaultCostTotalsEngine,
    product: str,
    warehouse: str,
    quantity: str,
    cost: str,
) -> None:
    source_identity = Identifier.new()
    totals.apply(
        Movement(
            identity=Identifier.new(),
            source_document_identity=source_identity,
            register_identity=inventory_register_configuration().register_identity,
            movement_type=MovementType.INCOME,
            dimensions=MovementDimensions.from_mapping(
                {"product": product, "warehouse": warehouse}
            ),
            resources=MovementResources.from_mapping({"quantity": Decimal(quantity)}),
            attributes=MovementAttributes.from_mapping({}),
            accounting_time=None,
        )
    )
    cost_totals.apply(
        CostMovement(
            identity=Identifier.new(),
            valuation_key=ValuationKey({"product": product, "warehouse": warehouse}),
            quantity=Decimal(quantity),
            cost=Decimal(cost),
            source_identity=source_identity,
            created_at=datetime.now(UTC),
        )
    )


def _execute(definition, registry):
    source = registry.get(definition.source)
    validated = DefaultReportValidator().validate(definition, source)
    compiled = DefaultReportCompiler().compile(validated)
    plan = DefaultReportExecutionPlanBuilder().build(compiled)
    return DefaultReportRuntime(registry).execute(plan)


def test_inventory_balance_report_metadata() -> None:
    assert INVENTORY_BALANCE_REPORT_IDENTITY == INVENTORY_BALANCE_REPORT_DEFINITION.identity
    assert INVENTORY_BALANCE_REPORT_DEFINITION.name == "Inventory Balance"
    assert INVENTORY_BALANCE_REPORT_DEFINITION.source is INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY
    assert INVENTORY_BALANCE_REPORT_DEFINITION.filters == ()
    assert [
        (item.name, item.source_field) for item in INVENTORY_BALANCE_REPORT_DEFINITION.dimensions
    ] == [
        ("product", "product"),
        ("warehouse", "warehouse"),
    ]
    assert [
        (item.name, item.aggregation.value, item.source_field)
        for item in INVENTORY_BALANCE_REPORT_DEFINITION.measures
    ] == [
        ("quantity", "sum", "quantity"),
        ("cost", "sum", "cost"),
    ]


def test_inventory_balance_report_validates_against_composed_source() -> None:
    totals, cost_totals = _state()
    registry = StandardConfigurationBootstrap().compose_inventory_reporting(totals, cost_totals)

    source = registry.get(INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY)
    validated = DefaultReportValidator().validate(INVENTORY_BALANCE_REPORT_DEFINITION, source)

    assert validated.definition is INVENTORY_BALANCE_REPORT_DEFINITION


def test_inventory_balance_report_executes_end_to_end() -> None:
    totals, cost_totals = _state()
    _add_inventory_state(totals, cost_totals, "P1", "W1", "7", "70")
    registry = StandardConfigurationBootstrap().compose_inventory_reporting(totals, cost_totals)

    dataset = _execute(INVENTORY_BALANCE_REPORT_DEFINITION, registry)

    assert [tuple(value.value for value in row.values.values()) for row in dataset.rows] == [
        ("P1", "W1", Decimal(7), Decimal(70))
    ]


def test_inventory_balance_report_has_deterministic_multiple_scope_order() -> None:
    totals, cost_totals = _state()
    _add_inventory_state(totals, cost_totals, "P2", "W2", "3", "30")
    _add_inventory_state(totals, cost_totals, "P1", "W2", "4", "40")
    _add_inventory_state(totals, cost_totals, "P1", "W1", "7", "70")
    registry = StandardConfigurationBootstrap().compose_inventory_reporting(totals, cost_totals)

    dataset = _execute(INVENTORY_BALANCE_REPORT_DEFINITION, registry)

    assert [(row["product"].value, row["warehouse"].value) for row in dataset.rows] == [
        ("P1", "W1"),
        ("P1", "W2"),
        ("P2", "W2"),
    ]


def test_inventory_balance_report_supports_generic_filter_without_changing_definition() -> None:
    totals, cost_totals = _state()
    _add_inventory_state(totals, cost_totals, "P1", "W1", "7", "70")
    _add_inventory_state(totals, cost_totals, "P2", "W2", "3", "30")
    registry = StandardConfigurationBootstrap().compose_inventory_reporting(totals, cost_totals)
    filtered = replace(
        INVENTORY_BALANCE_REPORT_DEFINITION,
        filters=(ReportFilter("warehouse", ReportFilterOperator.EQUALS, ReportValue("W2")),),
    )

    dataset = _execute(filtered, registry)

    assert [row["product"].value for row in dataset.rows] == ["P2"]
    assert INVENTORY_BALANCE_REPORT_DEFINITION.filters == ()


def test_inventory_balance_report_preserves_explicit_zero_cost() -> None:
    totals, cost_totals = _state()
    _add_inventory_state(totals, cost_totals, "P1", "W1", "7", "0")
    registry = StandardConfigurationBootstrap().compose_inventory_reporting(totals, cost_totals)

    dataset = _execute(INVENTORY_BALANCE_REPORT_DEFINITION, registry)

    assert dataset.rows[0]["cost"].value == Decimal(0)


def test_inventory_balance_report_empty_inventory_returns_zero_rows() -> None:
    totals, cost_totals = _state()
    registry = StandardConfigurationBootstrap().compose_inventory_reporting(totals, cost_totals)

    dataset = _execute(INVENTORY_BALANCE_REPORT_DEFINITION, registry)

    assert dataset.rows == ()


def test_inventory_balance_report_does_not_mutate_semantic_state() -> None:
    totals, cost_totals = _state()
    _add_inventory_state(totals, cost_totals, "P1", "W1", "7", "70")
    before_totals = totals.enumerate(inventory_register_configuration().register_identity)
    before_costs = cost_totals.enumerate()
    registry = StandardConfigurationBootstrap().compose_inventory_reporting(totals, cost_totals)

    _execute(INVENTORY_BALANCE_REPORT_DEFINITION, registry)

    assert totals.enumerate(inventory_register_configuration().register_identity) == before_totals
    assert cost_totals.enumerate() == before_costs
