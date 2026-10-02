from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from accore.platform.foundation import Identifier
from accore.platform.reporting.datasource import ReportDataSourceIdentity
from accore.platform.reporting.errors import ReportValidationError
from accore.platform.reporting.filters import ReportFilter


@dataclass(frozen=True, slots=True)
class ReportDimension:
    """Immutable analytical grouping axis over one source field."""

    name: str
    source_field: str
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ReportValidationError("Report dimension name must be non-empty")
        if not self.source_field:
            raise ReportValidationError("Report dimension source_field must be non-empty")


class ReportAggregation(StrEnum):
    """Aggregation functions supported by the first Reporting runtime."""

    SUM = "sum"
    COUNT = "count"
    MIN = "min"
    MAX = "max"


@dataclass(frozen=True, slots=True)
class ReportMeasure:
    """Immutable analytical measure definition."""

    name: str
    aggregation: ReportAggregation
    source_field: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ReportValidationError("Report measure name must be non-empty")
        if (
            self.aggregation
            in {
                ReportAggregation.SUM,
                ReportAggregation.MIN,
                ReportAggregation.MAX,
            }
            and not self.source_field
        ):
            raise ReportValidationError(
                f"{self.aggregation.value.upper()} measure requires source_field"
            )


@dataclass(frozen=True, slots=True)
class ReportDefinition:
    """Immutable declarative report definition."""

    identity: Identifier
    name: str
    source: ReportDataSourceIdentity
    filters: tuple[ReportFilter, ...]
    dimensions: tuple[ReportDimension, ...]
    measures: tuple[ReportMeasure, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.identity, Identifier):
            raise ReportValidationError("Report definition identity must be an Identifier")
        if not self.name:
            raise ReportValidationError("Report definition name must be non-empty")
        if not isinstance(self.source, ReportDataSourceIdentity) or not self.source.value:
            raise ReportValidationError("Report definition source identity must be non-empty")

        filters = tuple(self.filters)
        dimensions = tuple(self.dimensions)
        measures = tuple(self.measures)
        object.__setattr__(self, "filters", filters)
        object.__setattr__(self, "dimensions", dimensions)
        object.__setattr__(self, "measures", measures)

        dimension_names = tuple(item.name for item in dimensions)
        measure_names = tuple(item.name for item in measures)
        self._validate_unique_names("dimension", dimension_names)
        self._validate_unique_names("measure", measure_names)
        if set(dimension_names) & set(measure_names):
            raise ReportValidationError("Report dimension and measure names must not collide")
        if not dimensions and not measures:
            raise ReportValidationError(
                "Report definition requires at least one dimension or measure"
            )

    @staticmethod
    def _validate_unique_names(kind: str, names: tuple[str, ...]) -> None:
        if len(names) != len(set(names)):
            raise ReportValidationError(f"Report {kind} names must be unique")
