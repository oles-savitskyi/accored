from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from accore.platform.reporting.datasource import ReportDataSource
from accore.platform.reporting.definition import ReportAggregation, ReportDefinition
from accore.platform.reporting.errors import ReportValidationError
from accore.platform.reporting.schema import ReportSchema
from accore.platform.reporting.values import ReportDataType


@dataclass(frozen=True, slots=True)
class ValidatedReportDefinition:
    definition: ReportDefinition
    source_schema: ReportSchema


class ReportValidator(Protocol):
    def validate(
        self,
        definition: ReportDefinition,
        source: ReportDataSource,
    ) -> ValidatedReportDefinition: ...


class DefaultReportValidator:
    """Deterministic, side-effect-free report definition validator."""

    def validate(
        self,
        definition: ReportDefinition,
        source: ReportDataSource,
    ) -> ValidatedReportDefinition:
        schema = source.schema()
        field_names = {field.name for field in schema.fields}

        for report_filter in definition.filters:
            if report_filter.field not in field_names:
                raise ReportValidationError(f"Unknown report filter field: {report_filter.field}")
            self._validate_filter_values(
                report_filter.value, schema.field(report_filter.field).data_type
            )

        for dimension in definition.dimensions:
            if dimension.source_field not in field_names:
                raise ReportValidationError(
                    f"Unknown report dimension field: {dimension.source_field}"
                )

        for measure in definition.measures:
            if measure.aggregation is ReportAggregation.COUNT:
                continue
            assert measure.source_field is not None
            if measure.source_field not in field_names:
                raise ReportValidationError(f"Unknown report measure field: {measure.source_field}")
            source_type = schema.field(measure.source_field).data_type
            if measure.aggregation is ReportAggregation.SUM and source_type not in {
                ReportDataType.INTEGER,
                ReportDataType.DECIMAL,
            }:
                raise ReportValidationError(
                    f"Measure '{measure.name}' requires an integer or decimal source field"
                )
            if measure.aggregation in {
                ReportAggregation.MIN,
                ReportAggregation.MAX,
            } and source_type not in {
                ReportDataType.IDENTIFIER,
                ReportDataType.INTEGER,
                ReportDataType.DECIMAL,
                ReportDataType.STRING,
                ReportDataType.DATE,
                ReportDataType.DATETIME,
            }:
                raise ReportValidationError(
                    f"Measure '{measure.name}' requires an orderable source field"
                )

        return ValidatedReportDefinition(definition=definition, source_schema=schema)

    @staticmethod
    def _validate_filter_values(
        value: object,
        source_type: ReportDataType,
    ) -> None:
        values = value if isinstance(value, tuple) else (value,)
        for operand in values:
            if operand.value is None:
                raise ReportValidationError("None is not a valid Reporting filter operand")
            if operand.data_type is not source_type:
                raise ReportValidationError(
                    "Report filter operand type does not match source field"
                )
