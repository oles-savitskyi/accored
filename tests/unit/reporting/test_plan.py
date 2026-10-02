from accore.platform.foundation import Identifier
from accore.platform.reporting import (
    DefaultReportCompiler,
    DefaultReportExecutionPlanBuilder,
    DefaultReportValidator,
    ReportAggregateOperation,
    ReportAggregation,
    ReportDataSourceIdentity,
    ReportDataType,
    ReportDefinition,
    ReportDimension,
    ReportField,
    ReportFilter,
    ReportFilterOperation,
    ReportFilterOperator,
    ReportGroupOperation,
    ReportMeasure,
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

    def consistency(self):
        from accore.platform.reporting import ReportReadConsistency

        return ReportReadConsistency.SOURCE_LOCAL

    def read(self, request):
        return ()


def _compiled_definition(
    *,
    filters: tuple[ReportFilter, ...] = (),
    dimensions: tuple[ReportDimension, ...] = (),
    measures: tuple[ReportMeasure, ...] = (),
):
    definition = ReportDefinition(
        identity=Identifier("inventory"),
        name="Inventory",
        source=ReportDataSourceIdentity("inventory.balance"),
        filters=filters,
        dimensions=dimensions,
        measures=measures,
    )

    validated = DefaultReportValidator().validate(
        definition,
        Source(),
    )

    return DefaultReportCompiler().compile(validated)


def test_plan_builder_creates_filter_group_and_aggregate_operations() -> None:
    filters = (
        ReportFilter(
            "warehouse",
            ReportFilterOperator.EQUALS,
            ReportValue("A"),
        ),
    )
    dimensions = (ReportDimension("warehouse", "warehouse"),)
    measures = (ReportMeasure("cost", ReportAggregation.SUM, "cost"),)

    compiled = _compiled_definition(
        filters=filters,
        dimensions=dimensions,
        measures=measures,
    )

    plan = DefaultReportExecutionPlanBuilder().build(compiled)

    assert plan.filter_operation == ReportFilterOperation(filters)
    assert plan.group_operation == ReportGroupOperation(dimensions)
    assert plan.aggregate_operation == ReportAggregateOperation(measures)
    assert plan.compiled == compiled


def test_plan_builder_omits_filter_operation_when_no_filters() -> None:
    measures = (ReportMeasure("cost", ReportAggregation.SUM, "cost"),)

    compiled = _compiled_definition(measures=measures)

    plan = DefaultReportExecutionPlanBuilder().build(compiled)

    assert plan.filter_operation is None
    assert plan.group_operation is None
    assert plan.aggregate_operation == ReportAggregateOperation(measures)


def test_plan_builder_omits_group_operation_when_no_dimensions() -> None:
    measures = (ReportMeasure("cost", ReportAggregation.SUM, "cost"),)

    compiled = _compiled_definition(measures=measures)

    plan = DefaultReportExecutionPlanBuilder().build(compiled)

    assert plan.filter_operation is None
    assert plan.group_operation is None
    assert plan.aggregate_operation == ReportAggregateOperation(measures)


def test_plan_builder_preserves_dimension_and_measure_order() -> None:
    dimensions = (ReportDimension("warehouse", "warehouse"),)
    measures = (
        ReportMeasure("cost", ReportAggregation.SUM, "cost"),
        ReportMeasure("rows", ReportAggregation.COUNT),
    )

    compiled = _compiled_definition(
        dimensions=dimensions,
        measures=measures,
    )

    plan = DefaultReportExecutionPlanBuilder().build(compiled)

    assert plan.group_operation is not None
    assert plan.group_operation.dimensions == dimensions
    assert plan.aggregate_operation.measures == measures
