from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any, Protocol

from accore.platform.reporting.dataset import ReportDataset, ReportRow
from accore.platform.reporting.datasource import (
    ReportDataSourceRegistry,
    ReportDataSourceRequest,
)
from accore.platform.reporting.definition import ReportAggregation, ReportMeasure
from accore.platform.reporting.errors import ReportValidationError
from accore.platform.reporting.filters import ReportFilter, ReportFilterOperator
from accore.platform.reporting.plan import ReportExecutionPlan
from accore.platform.reporting.schema import ReportSchema
from accore.platform.reporting.values import ReportDataType, ReportValue


class ReportRuntime(Protocol):
    """Executable Reporting runtime boundary."""

    def execute(self, plan: ReportExecutionPlan) -> ReportDataset:
        """Execute an immutable plan and return an immutable dataset."""


class DefaultReportRuntime:
    """Reference runtime for filter, group, and aggregate operations."""

    def __init__(self, sources: ReportDataSourceRegistry) -> None:
        self._sources = sources

    def execute(self, plan: ReportExecutionPlan) -> ReportDataset:
        source = self._sources.get(plan.compiled.definition.source)
        self._validate_source_schema(source.schema(), plan.compiled.source_schema)

        filters = plan.filter_operation.filters if plan.filter_operation is not None else ()

        raw_rows = source.read(ReportDataSourceRequest(filters=filters))
        rows = tuple(
            self._validate_and_normalize_row(row, plan.compiled.source_schema) for row in raw_rows
        )

        if filters:
            rows = tuple(row for row in rows if self._matches_all(row, filters))

        dimensions = (
            tuple(dimension.source_field for dimension in plan.group_operation.dimensions)
            if plan.group_operation is not None
            else ()
        )

        measures = plan.aggregate_operation.measures

        result_rows = self._aggregate(
            rows,
            dimensions,
            measures,
            plan,
        )

        return ReportDataset(plan.compiled.output_schema, result_rows)

    @staticmethod
    def _validate_source_schema(actual: ReportSchema, expected: ReportSchema) -> None:
        if actual != expected:
            raise ReportValidationError(
                "Reporting data source schema changed after report compilation"
            )

    @staticmethod
    def _validate_and_normalize_row(
        row: ReportRow,
        schema: ReportSchema,
    ) -> Mapping[str, ReportValue]:
        expected_fields = {field.name: field.data_type for field in schema.fields}
        if set(row.values) != set(expected_fields):
            raise ReportValidationError(
                "Reporting data source row fields do not match its declared schema"
            )

        for field_name, expected_type in expected_fields.items():
            value = row.values[field_name]
            if value.value is not None and value.data_type is not expected_type:
                raise ReportValidationError(
                    f"Reporting data source field '{field_name}' has an invalid value type"
                )

        return row.values

    @staticmethod
    def _matches_all(
        row: Mapping[str, ReportValue],
        filters: Sequence[ReportFilter],
    ) -> bool:
        for report_filter in filters:
            actual = row.get(report_filter.field)

            if actual is None or actual.value is None:
                return False

            expected = report_filter.value
            operator = report_filter.operator

            if operator is ReportFilterOperator.EQUALS:
                if actual != expected:
                    return False
                continue

            if operator is ReportFilterOperator.NOT_EQUALS:
                if actual == expected:
                    return False
                continue

            if operator is ReportFilterOperator.IN:
                if not isinstance(expected, tuple):
                    raise ReportValidationError(
                        "IN filter requires a tuple of ReportValue operands"
                    )

                if actual not in expected:
                    return False
                continue

            if not isinstance(expected, ReportValue):
                raise ReportValidationError(
                    f"{operator.value} filter requires a single ReportValue operand"
                )

            if not DefaultReportRuntime._matches_relational(
                actual,
                expected,
                operator,
            ):
                return False

        return True

    @staticmethod
    def _matches_relational(
        actual: ReportValue,
        expected: ReportValue,
        operator: ReportFilterOperator,
    ) -> bool:
        if actual.value is None or expected.value is None:
            return False

        actual_value: Any = actual.value
        expected_value: Any = expected.value

        if operator is ReportFilterOperator.LESS_THAN:
            return bool(actual_value < expected_value)

        if operator is ReportFilterOperator.LESS_THAN_OR_EQUAL:
            return bool(actual_value <= expected_value)

        if operator is ReportFilterOperator.GREATER_THAN:
            return bool(actual_value > expected_value)

        if operator is ReportFilterOperator.GREATER_THAN_OR_EQUAL:
            return bool(actual_value >= expected_value)

        raise ReportValidationError(f"Unsupported relational filter operator: {operator.value}")

    @staticmethod
    def _aggregate(
        rows: Sequence[Mapping[str, ReportValue]],
        dimensions: tuple[str, ...],
        measures: Sequence[ReportMeasure],
        plan: ReportExecutionPlan,
    ) -> tuple[ReportRow, ...]:
        groups: dict[
            tuple[ReportValue, ...],
            list[Mapping[str, ReportValue]],
        ] = defaultdict(list)

        if dimensions:
            for row in rows:
                key = tuple(row[field] for field in dimensions)
                groups[key].append(row)
        else:
            groups[()] = list(rows)

        result: list[ReportRow] = []

        for key, group in groups.items():
            values: dict[str, ReportValue] = {}

            for index, _field in enumerate(dimensions):
                dimension_name = plan.compiled.definition.dimensions[index].name
                values[dimension_name] = key[index]

            for measure in measures:
                values[measure.name] = DefaultReportRuntime._compute_aggregate(
                    measure,
                    group,
                    plan.compiled.source_schema,
                )

            result.append(ReportRow(values))

        result.sort(
            key=lambda row: DefaultReportRuntime._canonical_key(
                row,
                dimensions,
                plan,
            )
        )

        return tuple(result)

    @staticmethod
    def _compute_aggregate(
        measure: ReportMeasure,
        rows: Sequence[Mapping[str, ReportValue]],
        source_schema: ReportSchema,
    ) -> ReportValue:
        if measure.aggregation is ReportAggregation.COUNT:
            return ReportValue(len(rows))

        assert measure.source_field is not None

        source_type = source_schema.field(measure.source_field).data_type
        values = [row[measure.source_field] for row in rows]
        non_null_values = [value for value in values if value.value is not None]

        if measure.aggregation is ReportAggregation.SUM:
            if source_type not in {ReportDataType.INTEGER, ReportDataType.DECIMAL}:
                raise ReportValidationError("SUM requires integer or Decimal values")

            if not non_null_values:
                return ReportValue(0 if source_type is ReportDataType.INTEGER else Decimal(0))

            if source_type is ReportDataType.INTEGER:
                integer_values: list[int] = []
                for value in non_null_values:
                    if not isinstance(value.value, int) or isinstance(value.value, bool):
                        raise ReportValidationError(
                            f"Measure '{measure.name}' contains a non-integer value"
                        )
                    integer_values.append(value.value)
                return ReportValue(sum(integer_values))

            decimal_values: list[Decimal] = []
            for value in non_null_values:
                if isinstance(value.value, Decimal):
                    decimal_values.append(value.value)
                elif isinstance(value.value, int) and not isinstance(value.value, bool):
                    decimal_values.append(Decimal(value.value))
                else:
                    raise ReportValidationError(
                        f"Measure '{measure.name}' contains a non-decimal value"
                    )

            return ReportValue(sum(decimal_values, Decimal(0)))

        if measure.aggregation in {ReportAggregation.MIN, ReportAggregation.MAX}:
            if source_type not in {
                ReportDataType.IDENTIFIER,
                ReportDataType.INTEGER,
                ReportDataType.DECIMAL,
                ReportDataType.STRING,
                ReportDataType.DATE,
                ReportDataType.DATETIME,
            }:
                raise ReportValidationError(
                    f"{measure.aggregation.value.upper()} requires an orderable source field"
                )
            if not non_null_values:
                raise ReportValidationError(
                    f"Cannot compute {measure.aggregation.value} without a non-null value"
                )

            if measure.aggregation is ReportAggregation.MIN:
                return DefaultReportRuntime._min_value(non_null_values)

            return DefaultReportRuntime._max_value(non_null_values)

        raise ReportValidationError(f"Unsupported aggregation: {measure.aggregation.value}")

    @staticmethod
    def _min_value(values: Sequence[ReportValue]) -> ReportValue:
        current = values[0]

        for candidate in values[1:]:
            if DefaultReportRuntime._compare_values(candidate, current) < 0:
                current = candidate

        return current

    @staticmethod
    def _max_value(values: Sequence[ReportValue]) -> ReportValue:
        current = values[0]

        for candidate in values[1:]:
            if DefaultReportRuntime._compare_values(candidate, current) > 0:
                current = candidate

        return current

    @staticmethod
    def _compare_values(
        left: ReportValue,
        right: ReportValue,
    ) -> int:
        if left.value is None or right.value is None:
            raise ReportValidationError("Cannot compare null ReportValue instances")

        left_value: Any = left.value
        right_value: Any = right.value

        if left_value < right_value:
            return -1

        if left_value > right_value:
            return 1

        return 0

    @staticmethod
    def _canonical_key(
        row: ReportRow,
        dimensions: tuple[str, ...],
        plan: ReportExecutionPlan,
    ) -> tuple[tuple[str, Any], ...]:
        return tuple(
            DefaultReportRuntime._value_sort_key(
                row[plan.compiled.definition.dimensions[index].name],
            )
            for index, _ in enumerate(dimensions)
        )

    @staticmethod
    def _value_sort_key(
        value: ReportValue,
    ) -> tuple[str, Any]:
        if value.value is None:
            return ("null", "")

        if value.data_type.value == "identifier":
            return (value.data_type.value, str(value.value))

        return (value.data_type.value, value.value)
