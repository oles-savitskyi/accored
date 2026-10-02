import pytest

from accore.platform.foundation import Identifier
from accore.platform.reporting import (
    ReportAggregation,
    ReportDataSourceIdentity,
    ReportDefinition,
    ReportDimension,
    ReportFilter,
    ReportFilterOperator,
    ReportMeasure,
    ReportValidationError,
    ReportValue,
)


def test_count_measure_does_not_require_source_field() -> None:
    measure = ReportMeasure(name="rows", aggregation=ReportAggregation.COUNT)

    assert measure.source_field is None


def test_non_count_measure_requires_source_field() -> None:
    with pytest.raises(ReportValidationError):
        ReportMeasure(name="amount", aggregation=ReportAggregation.SUM)


def test_report_definition_normalizes_sequences_to_tuples() -> None:
    definition = ReportDefinition(
        identity=Identifier("inventory"),
        name="inventory",
        source=ReportDataSourceIdentity("inventory.balance"),
        filters=[
            ReportFilter("warehouse", ReportFilterOperator.EQUALS, ReportValue("A")),
        ],
        dimensions=[
            ReportDimension("warehouse", "warehouse"),
        ],
        measures=[ReportMeasure("amount", ReportAggregation.SUM, "amount")],
    )

    assert isinstance(definition.filters, tuple)
    assert isinstance(definition.dimensions, tuple)
    assert isinstance(definition.measures, tuple)
    assert definition.measures[0].source_field == "amount"
