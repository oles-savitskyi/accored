from decimal import Decimal

import pytest

from accore.platform.foundation import Identifier
from accore.platform.reporting.compile import (
    CompiledReport,
    DefaultReportCompiler,
)
from accore.platform.reporting.dataset import ReportRow
from accore.platform.reporting.datasource import ReportDataSourceIdentity
from accore.platform.reporting.definition import (
    ReportAggregation,
    ReportDefinition,
    ReportDimension,
    ReportMeasure,
)
from accore.platform.reporting.errors import ReportValidationError
from accore.platform.reporting.schema import ReportField, ReportSchema
from accore.platform.reporting.validation import DefaultReportValidator
from accore.platform.reporting.values import ReportDataType, ReportValue


class Source:
    identity = ReportDataSourceIdentity("inventory.balance")

    def __init__(self) -> None:
        self.read_called = False

    def schema(self) -> ReportSchema:
        return ReportSchema(
            (
                ReportField("warehouse", ReportDataType.STRING),
                ReportField("cost", ReportDataType.DECIMAL),
                ReportField("quantity", ReportDataType.INTEGER),
            )
        )

    def consistency(self):
        from accore.platform.reporting import ReportReadConsistency

        return ReportReadConsistency.SOURCE_LOCAL

    def read(self, request):
        self.read_called = True
        return (
            ReportRow(
                {
                    "warehouse": ReportValue("A"),
                    "cost": ReportValue(Decimal("10.00")),
                    "quantity": ReportValue(2),
                }
            ),
        )


def _definition() -> ReportDefinition:
    return ReportDefinition(
        identity=Identifier("inventory"),
        name="Inventory balance",
        source=ReportDataSourceIdentity("inventory.balance"),
        filters=(),
        dimensions=(ReportDimension("warehouse", "warehouse"),),
        measures=(
            ReportMeasure("cost", ReportAggregation.SUM, "cost"),
            ReportMeasure("rows", ReportAggregation.COUNT),
        ),
    )


def test_validator_returns_validated_definition_with_source_schema() -> None:
    source = Source()

    validated = DefaultReportValidator().validate(
        _definition(),
        source,
    )

    assert validated.definition == _definition()
    assert validated.source_schema == source.schema()
    assert not source.read_called


def test_compiler_produces_compiled_report() -> None:
    source = Source()
    validated = DefaultReportValidator().validate(_definition(), source)

    compiled = DefaultReportCompiler().compile(validated)

    assert isinstance(compiled, CompiledReport)
    assert compiled.definition == _definition()
    assert compiled.source_schema == source.schema()

    assert compiled.output_schema == ReportSchema(
        (
            ReportField("warehouse", ReportDataType.STRING),
            ReportField("cost", ReportDataType.DECIMAL),
            ReportField("rows", ReportDataType.INTEGER),
        )
    )

    assert not source.read_called


def test_compiler_does_not_execute_data_source() -> None:
    source = Source()
    validated = DefaultReportValidator().validate(_definition(), source)

    DefaultReportCompiler().compile(validated)

    assert source.read_called is False


def test_validator_rejects_unknown_dimension_field() -> None:
    source = Source()

    definition = ReportDefinition(
        identity=Identifier("inventory"),
        name="Inventory",
        source=ReportDataSourceIdentity("inventory.balance"),
        filters=(),
        dimensions=(ReportDimension("warehouse", "missing"),),
        measures=(),
    )

    with pytest.raises(
        ReportValidationError,
        match="Unknown report dimension field",
    ):
        DefaultReportValidator().validate(definition, source)


def test_validator_rejects_unknown_measure_field() -> None:
    source = Source()

    definition = ReportDefinition(
        identity=Identifier("inventory"),
        name="Inventory",
        source=ReportDataSourceIdentity("inventory.balance"),
        filters=(),
        dimensions=(),
        measures=(ReportMeasure("cost", ReportAggregation.SUM, "missing"),),
    )

    with pytest.raises(
        ReportValidationError,
        match="Unknown report measure field",
    ):
        DefaultReportValidator().validate(definition, source)


def test_validator_rejects_sum_over_string_field() -> None:
    source = Source()

    definition = ReportDefinition(
        identity=Identifier("inventory"),
        name="Inventory",
        source=ReportDataSourceIdentity("inventory.balance"),
        filters=(),
        dimensions=(),
        measures=(ReportMeasure("warehouse", ReportAggregation.SUM, "warehouse"),),
    )

    with pytest.raises(
        ReportValidationError,
        match="requires an integer or decimal source field",
    ):
        DefaultReportValidator().validate(definition, source)
