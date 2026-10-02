from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from accore.platform.reporting.compile import CompiledReport
from accore.platform.reporting.definition import ReportDimension, ReportMeasure
from accore.platform.reporting.filters import ReportFilter


@dataclass(frozen=True, slots=True)
class ReportFilterOperation:
    """Immutable filter stage of a report execution plan."""

    filters: tuple[ReportFilter, ...]


@dataclass(frozen=True, slots=True)
class ReportGroupOperation:
    """Immutable grouping stage of a report execution plan."""

    dimensions: tuple[ReportDimension, ...]


@dataclass(frozen=True, slots=True)
class ReportAggregateOperation:
    """Immutable aggregation stage of a report execution plan."""

    measures: tuple[ReportMeasure, ...]


ReportPlanOperation = ReportFilterOperation | ReportGroupOperation | ReportAggregateOperation


@dataclass(frozen=True, slots=True)
class ReportExecutionPlan:
    """Immutable deterministic execution plan for a compiled report."""

    compiled: CompiledReport
    filter_operation: ReportFilterOperation | None
    group_operation: ReportGroupOperation | None
    aggregate_operation: ReportAggregateOperation


class ReportExecutionPlanBuilder(Protocol):
    """Build an immutable execution plan from compiled report metadata."""

    def build(
        self,
        compiled: CompiledReport,
    ) -> ReportExecutionPlan: ...


@dataclass(frozen=True, slots=True)
class DefaultReportExecutionPlanBuilder:
    """Reference deterministic execution-plan builder."""

    def build(
        self,
        compiled: CompiledReport,
    ) -> ReportExecutionPlan:
        definition = compiled.definition

        filter_operation = ReportFilterOperation(definition.filters) if definition.filters else None

        group_operation = (
            ReportGroupOperation(definition.dimensions) if definition.dimensions else None
        )

        aggregate_operation = ReportAggregateOperation(
            definition.measures,
        )

        return ReportExecutionPlan(
            compiled=compiled,
            filter_operation=filter_operation,
            group_operation=group_operation,
            aggregate_operation=aggregate_operation,
        )
