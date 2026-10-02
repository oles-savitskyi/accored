from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.reporting import (
    DefaultReportCompiler,
    DefaultReportDataSourceRegistry,
    DefaultReportExecutionPlanBuilder,
    DefaultReportRuntime,
    DefaultReportValidator,
    ReportAggregation,
    ReportDataset,
    ReportDataSource,
    ReportDataSourceIdentity,
    ReportDataSourceRequest,
    ReportDataType,
    ReportDefinition,
    ReportDimension,
    ReportField,
    ReportFilter,
    ReportFilterOperator,
    ReportMeasure,
    ReportReadConsistency,
    ReportRow,
    ReportSchema,
    ReportValue,
)


class Source:
    identity = ReportDataSourceIdentity("inventory.balance")

    def schema(self) -> ReportSchema:
        return ReportSchema(
            (
                ReportField("warehouse", ReportDataType.STRING),
                ReportField("cost", ReportDataType.DECIMAL),
            )
        )

    def consistency(self) -> ReportReadConsistency:
        return ReportReadConsistency.SOURCE_LOCAL

    def read(self, request: ReportDataSourceRequest) -> tuple[ReportRow, ...]:
        return (
            ReportRow(
                {
                    "warehouse": ReportValue("B"),
                    "cost": ReportValue(Decimal("2.00")),
                }
            ),
            ReportRow(
                {
                    "warehouse": ReportValue("A"),
                    "cost": ReportValue(Decimal("3.00")),
                }
            ),
            ReportRow(
                {
                    "warehouse": ReportValue("A"),
                    "cost": ReportValue(Decimal("4.00")),
                }
            ),
        )


def _runtime() -> DefaultReportRuntime:
    registry = DefaultReportDataSourceRegistry()
    registry.register(Source())
    return DefaultReportRuntime(registry)


def test_runtime_filters_groups_aggregates_and_orders_deterministically() -> None:
    definition = ReportDefinition(
        identity=Identifier("inventory"),
        name="inventory",
        source=ReportDataSourceIdentity("inventory.balance"),
        filters=(
            ReportFilter(
                "cost",
                ReportFilterOperator.GREATER_THAN_OR_EQUAL,
                ReportValue(Decimal(2)),
            ),
        ),
        dimensions=(ReportDimension("warehouse", "warehouse"),),
        measures=(ReportMeasure("cost", ReportAggregation.SUM, "cost"),),
    )
    validated = DefaultReportValidator().validate(
        definition,
        Source(),
    )
    compiled = DefaultReportCompiler().compile(validated)
    plan = DefaultReportExecutionPlanBuilder().build(compiled)

    dataset = _runtime().execute(plan)

    assert [row["warehouse"].value for row in dataset.rows] == ["A", "B"]
    assert [row["cost"].value for row in dataset.rows] == [Decimal("7.00"), Decimal("2.00")]


def test_runtime_count_is_input_row_count() -> None:
    definition = ReportDefinition(
        identity=Identifier("inventory"),
        name="inventory",
        source=ReportDataSourceIdentity("inventory.balance"),
        filters=(
            ReportFilter(
                "cost",
                ReportFilterOperator.GREATER_THAN_OR_EQUAL,
                ReportValue(Decimal(2)),
            ),
        ),
        dimensions=(ReportDimension("warehouse", "warehouse"),),
        measures=(ReportMeasure("rows", ReportAggregation.COUNT),),
    )
    validated = DefaultReportValidator().validate(
        definition,
        Source(),
    )
    compiled = DefaultReportCompiler().compile(validated)
    plan = DefaultReportExecutionPlanBuilder().build(compiled)

    dataset = _runtime().execute(plan)

    assert [row["rows"].value for row in dataset.rows] == [2, 1]


class NullableSource:
    identity = ReportDataSourceIdentity("inventory.nullable")

    def __init__(self, rows: tuple[ReportRow, ...]) -> None:
        self._rows = rows

    def schema(self) -> ReportSchema:
        return ReportSchema(
            (
                ReportField("warehouse", ReportDataType.STRING),
                ReportField("cost", ReportDataType.DECIMAL),
            )
        )

    def consistency(self) -> ReportReadConsistency:
        return ReportReadConsistency.SOURCE_LOCAL

    def read(self, request: ReportDataSourceRequest) -> tuple[ReportRow, ...]:
        return self._rows


def _execute(
    source: ReportDataSource,
    definition: ReportDefinition,
) -> ReportDataset:
    registry = DefaultReportDataSourceRegistry()
    registry.register(source)
    validated = DefaultReportValidator().validate(definition, source)
    compiled = DefaultReportCompiler().compile(validated)
    plan = DefaultReportExecutionPlanBuilder().build(compiled)
    return DefaultReportRuntime(registry).execute(plan)


def test_runtime_empty_dimensioned_input_returns_no_rows() -> None:
    source = NullableSource(())
    definition = ReportDefinition(
        identity=Identifier("inventory"),
        name="inventory",
        source=source.identity,
        filters=(),
        dimensions=(ReportDimension("warehouse", "warehouse"),),
        measures=(ReportMeasure("rows", ReportAggregation.COUNT),),
    )

    dataset = _execute(source, definition)

    assert dataset.rows == ()


def test_runtime_empty_aggregate_only_input_returns_one_group() -> None:
    source = NullableSource(())
    definition = ReportDefinition(
        identity=Identifier("inventory"),
        name="inventory",
        source=source.identity,
        filters=(),
        dimensions=(),
        measures=(
            ReportMeasure("rows", ReportAggregation.COUNT),
            ReportMeasure("cost", ReportAggregation.SUM, "cost"),
        ),
    )

    dataset = _execute(source, definition)

    assert len(dataset.rows) == 1
    assert dataset.rows[0]["rows"].value == 0
    assert dataset.rows[0]["cost"].value == Decimal(0)


class IntegerSource:
    identity = ReportDataSourceIdentity("inventory.integer")

    def schema(self) -> ReportSchema:
        return ReportSchema((ReportField("amount", ReportDataType.INTEGER),))

    def consistency(self) -> ReportReadConsistency:
        return ReportReadConsistency.SOURCE_LOCAL

    def read(self, request: ReportDataSourceRequest) -> tuple[ReportRow, ...]:
        return ()


def test_runtime_integer_sum_empty_group_preserves_integer_type() -> None:
    source = IntegerSource()
    definition = ReportDefinition(
        identity=Identifier("inventory"),
        name="inventory",
        source=source.identity,
        filters=(),
        dimensions=(),
        measures=(ReportMeasure("amount", ReportAggregation.SUM, "amount"),),
    )

    dataset = _execute(source, definition)

    assert dataset.rows[0]["amount"].value == 0
    assert dataset.rows[0]["amount"].data_type is ReportDataType.INTEGER


def test_runtime_sum_ignores_null_values() -> None:
    source = NullableSource(
        (
            ReportRow({"warehouse": ReportValue("A"), "cost": ReportValue(None)}),
            ReportRow({"warehouse": ReportValue("A"), "cost": ReportValue(Decimal("2.50"))}),
        )
    )
    definition = ReportDefinition(
        identity=Identifier("inventory"),
        name="inventory",
        source=source.identity,
        filters=(),
        dimensions=(ReportDimension("warehouse", "warehouse"),),
        measures=(ReportMeasure("cost", ReportAggregation.SUM, "cost"),),
    )

    dataset = _execute(source, definition)

    assert dataset.rows[0]["cost"].value == Decimal("2.50")


def test_runtime_min_max_ignore_null_values() -> None:
    source = NullableSource(
        (
            ReportRow({"warehouse": ReportValue("A"), "cost": ReportValue(None)}),
            ReportRow({"warehouse": ReportValue("A"), "cost": ReportValue(Decimal("2.50"))}),
            ReportRow({"warehouse": ReportValue("A"), "cost": ReportValue(Decimal("4.00"))}),
        )
    )
    definition = ReportDefinition(
        identity=Identifier("inventory"),
        name="inventory",
        source=source.identity,
        filters=(),
        measures=(
            ReportMeasure("minimum", ReportAggregation.MIN, "cost"),
            ReportMeasure("maximum", ReportAggregation.MAX, "cost"),
        ),
        dimensions=(ReportDimension("warehouse", "warehouse"),),
    )

    dataset = _execute(source, definition)

    assert dataset.rows[0]["minimum"].value == Decimal("2.50")
    assert dataset.rows[0]["maximum"].value == Decimal("4.00")


def test_runtime_null_filter_value_never_matches_not_equals() -> None:
    source = NullableSource(
        (
            ReportRow({"warehouse": ReportValue("A"), "cost": ReportValue(None)}),
            ReportRow({"warehouse": ReportValue("A"), "cost": ReportValue(Decimal("2.50"))}),
        )
    )
    definition = ReportDefinition(
        identity=Identifier("inventory"),
        name="inventory",
        source=source.identity,
        filters=(
            ReportFilter(
                "cost",
                ReportFilterOperator.NOT_EQUALS,
                ReportValue(Decimal("2.00")),
            ),
        ),
        dimensions=(ReportDimension("warehouse", "warehouse"),),
        measures=(ReportMeasure("rows", ReportAggregation.COUNT),),
    )

    dataset = _execute(source, definition)

    assert dataset.rows[0]["rows"].value == 1
