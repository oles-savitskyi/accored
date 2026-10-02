from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from accore.platform.reporting.definition import ReportAggregation, ReportDefinition
from accore.platform.reporting.schema import ReportField, ReportSchema
from accore.platform.reporting.validation import ValidatedReportDefinition
from accore.platform.reporting.values import ReportDataType


@dataclass(frozen=True, slots=True)
class CompiledReport:
    """Immutable compiled representation of a validated report definition."""

    definition: ReportDefinition
    source_schema: ReportSchema
    output_schema: ReportSchema


class ReportCompiler(Protocol):
    """Compilation boundary from validated definition to immutable report metadata."""

    def compile(
        self,
        validated: ValidatedReportDefinition,
    ) -> CompiledReport: ...


@dataclass(frozen=True, slots=True)
class DefaultReportCompiler:
    """Reference compiler for validated Reporting definitions."""

    def compile(
        self,
        validated: ValidatedReportDefinition,
    ) -> CompiledReport:
        definition = validated.definition
        schema = validated.source_schema

        output_fields: list[ReportField] = []

        for dimension in definition.dimensions:
            source_field = schema.field(dimension.source_field)
            output_fields.append(
                ReportField(
                    dimension.name,
                    source_field.data_type,
                )
            )

        for measure in definition.measures:
            if measure.aggregation is ReportAggregation.COUNT:
                output_type = ReportDataType.INTEGER
            else:
                assert measure.source_field is not None
                output_type = schema.field(measure.source_field).data_type

            output_fields.append(
                ReportField(
                    measure.name,
                    output_type,
                )
            )

        return CompiledReport(
            definition=definition,
            source_schema=schema,
            output_schema=ReportSchema(tuple(output_fields)),
        )
